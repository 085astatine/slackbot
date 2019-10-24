# -*- coding: utf-8 -*-

import collections
import datetime
import enum
import logging
import pathlib
import re
import shutil
import tempfile
import threading
import time
import queue
from typing import (
        Deque, Generic, MutableMapping, NamedTuple, Optional, TypeVar, Union)
import requests
from .. import Option, OptionList


class DownloadThreadOption(NamedTuple):
    chunk_size: int
    report_interval: float
    speedmeter_size: int
    file_permission: Optional[int]

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['DownloadThreadOption']:
        # parse permission (format 0oXXX)
        def read_permission(value: str) -> Optional[int]:
            match = re.match('0o(?P<permission>[0-7]{3})', value)
            if match:
                return int(match.group('permission'), base=8)
            return None

        return OptionList(
            DownloadThreadOption,
            name,
            [Option('chunk_size',
                    default=1024,
                    type=int,
                    help='data chank size (byte) for streaming download'),
             Option('report_interval',
                    default=60.0,
                    type=float,
                    help=('interval in seconds'
                          ' between download progress reports')),
             Option('speedmeter_size',
                    default=100,
                    type=int,
                    help=('number of data chunks'
                          ' for download speed measurement')),
             Option('file_permission',
                    action=read_permission,
                    default='0o644',
                    help='downloaded file permission (format: 0oXXX)')],
            help=help)


class SpeedMeter:
    class Data(NamedTuple):
        value: float
        time: float

    def __init__(self, size: int) -> None:
        self._deque: Deque[SpeedMeter.Data] = collections.deque(maxlen=size)

    def push(self, value: float) -> None:
        self._deque.append(SpeedMeter.Data(
                value=value,
                time=time.perf_counter()))

    def speed(self) -> Optional[float]:
        if len(self._deque) == 0:
            return None
        valuedelta = self._deque[-1].value - self._deque[0].value
        timedelta = self._deque[-1].time - self._deque[0].time
        return valuedelta / timedelta if timedelta != 0 else None


class ProgressReport(NamedTuple):
    file_size: Optional[int]
    downloaded_size: int
    elapsed_time: float
    speed: Optional[float]

    @property
    def remaining_size(self) -> Optional[int]:
        if self.file_size is not None:
            return self.file_size - self.downloaded_size
        else:
            return None

    @property
    def progress_rate(self) -> Optional[float]:
        if self.file_size is not None and self.file_size > 0:
            return self.downloaded_size / self.file_size
        else:
            return None

    @property
    def average_speed(self) -> Optional[float]:
        if self.elapsed_time > 0:
            return self.downloaded_size / self.elapsed_time
        else:
            return None

    @property
    def remaining_time(self) -> Optional[float]:
        if (self.remaining_size is not None
                and self.speed is not None
                and self.speed > 0):
            return self.remaining_size / self.speed
        else:
            return None


class Progress:
    def __init__(
            self,
            file_size: Optional[int],
            speedmeter_size: int) -> None:
        self._start_time = time.perf_counter()
        self._latest_time = self._start_time
        self._file_size = file_size
        self._downloaded_size = 0
        self._speedmeter = SpeedMeter(speedmeter_size)
        self._speedmeter.push(0)

    def update(self, received_size: int) -> None:
        self._downloaded_size += received_size
        self._latest_time = time.perf_counter()
        self._speedmeter.push(self._downloaded_size)

    def is_completed(self) -> bool:
        return (self._file_size is None
                or self._file_size == self._downloaded_size)

    def report(self) -> ProgressReport:
        return ProgressReport(
                file_size=self._file_size,
                downloaded_size=self._downloaded_size,
                elapsed_time=self._latest_time - self._start_time,
                speed=self._speedmeter.speed())


class ProgressReportTimer:
    def __init__(self, interval: float) -> None:
        self._last = time.perf_counter()
        self._interval = interval

    def check(self) -> bool:
        current = time.perf_counter()
        if current - self._last >= self._interval:
            self._last = current
            return True
        return False


class DownloadException(Exception):
    def __init__(self, response: requests.models.Response) -> None:
        self._response = response

    def __str__(self) -> str:
        return 'status code [{0}]'.format(self._response.status_code)


class DownloadReportType(enum.Enum):
    START = enum.auto()
    PROGRESS = enum.auto()
    FINISH = enum.auto()
    ERROR = enum.auto()


ReportInfo = TypeVar('ReportInfo')


class DownloadReport(Generic[ReportInfo]):
    def __init__(
            self,
            type: DownloadReportType,
            info: ReportInfo,
            url: str,
            path: pathlib.Path,
            temp_path: Optional[pathlib.Path],
            final_url: Optional[str],
            response_header: Optional[MutableMapping[str, str]],
            progress: ProgressReport,
            saved_path: Optional[pathlib.Path] = None,
            error: Optional[Exception] = None) -> None:
        self.type = type
        self.info = info
        self.url = url
        self.path = path
        self.temp_path = temp_path
        self.final_url = final_url
        self.response_header = response_header
        self.progress = progress
        self.saved_path = saved_path
        self.error = error

    def __repr__(self) -> str:
        keys = ['type', 'info', 'url', 'path', 'temp_path', 'final_url',
                'response_header', 'progress', 'saved_path', 'error']
        return '{0}.{1}({2})'.format(
                self.__class__.__module__,
                self.__class__.__name__,
                ', '.join('{0}={1}'.format(key, repr(getattr(self, key)))
                          for key in keys))

    @staticmethod
    def format_bytes(
                value: Union[int, float, None],
                precision: int = 2) -> str:
        if value is None:
            return '-B'
        prefix_list = ('', 'Ki', 'Mi', 'Gi', 'Ti')
        integer_part = value
        unit = 1
        unit_index = 0
        while integer_part >= 1024 and unit_index < len(prefix_list) - 1:
            integer_part //= 1024
            unit *= 1024
            unit_index += 1
        return ('{{value:.{precision}f}}{{unit}}B'
                .format(precision=precision)
                .format(value=value / unit, unit=prefix_list[unit_index]))


class Reporter(Generic[ReportInfo]):
    def __init__(
            self,
            info: ReportInfo,
            report_queue: 'queue.Queue[DownloadReport[ReportInfo]]',
            url: str,
            path: pathlib.Path) -> None:
        self._report_queue = report_queue
        # report parameter
        self._info = info
        self._url = url
        self._path = path
        self._final_url: Optional[str] = None
        self._temp_path: Optional[pathlib.Path] = None
        self._response_header: Optional[MutableMapping[str, str]] = None
        self._progress = ProgressReport(
                file_size=None,
                downloaded_size=0,
                elapsed_time=0.,
                speed=None)
        self._saved_path: Optional[pathlib.Path] = None
        self._error: Optional[Exception] = None

    def start(
            self,
            temp_path: pathlib.Path,
            response: requests.Response) -> None:
        self._temp_path = temp_path
        self._final_url = response.url
        self._response_header = response.headers
        # report
        self.report(DownloadReportType.START)

    def progress(
            self,
            progress: ProgressReport) -> None:
        self._progress = progress
        # report
        self.report(DownloadReportType.PROGRESS)

    def finish(
            self,
            saved_path: pathlib.Path,
            progress: ProgressReport) -> None:
        self._saved_path = saved_path
        self._progress = progress
        # report
        self.report(DownloadReportType.FINISH)

    def error(self, error: Exception) -> None:
        self._error = error
        # report
        self.report(DownloadReportType.ERROR)

    def create_report(
            self,
            type: DownloadReportType) -> DownloadReport[ReportInfo]:
        return DownloadReport(
                type=type,
                info=self._info,
                url=self._url,
                path=self._path,
                temp_path=self._temp_path,
                final_url=self._final_url,
                response_header=self._response_header,
                progress=self._progress,
                saved_path=self._saved_path,
                error=self._error)

    def report(self, type: DownloadReportType) -> None:
        self._report_queue.put(self.create_report(type))


_move_file_lock = threading.Lock()


class DownloadThread(threading.Thread, Generic[ReportInfo]):
    def __init__(
                self,
                info: ReportInfo,
                report_queue: 'queue.Queue[DownloadReport[ReportInfo]]',
                path: pathlib.Path,
                url: str,
                option: DownloadThreadOption) -> None:
        super().__init__()
        self._info = info
        self._report_queue = report_queue
        self._path = path
        self._url = url
        self._option = option

    def run(self) -> None:
        # reporter
        reporter = Reporter(
                info=self._info,
                report_queue=self._report_queue,
                url=self._url,
                path=self._path)
        # mkdir
        if not self._path.parent.exists():
            self._path.parent.mkdir(parents=True)
        # download
        temp_file_path: Optional[pathlib.Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='wb',
                    delete=False,
                    dir=self._path.parent.as_posix()) as temp_file:
                temp_file_path = pathlib.Path(temp_file.name)
                # streaming download
                response = requests.get(self._url, stream=True)
                # status code check
                response.raise_for_status()
                # start report
                reporter.start(
                        temp_path=temp_file_path,
                        response=response)
                # progress
                content_length = response.headers.get('Content-Length', '')
                progress = Progress(
                        file_size=(int(content_length)
                                   if content_length.isdigit() else None),
                        speedmeter_size=self._option.speedmeter_size)
                progress_timer = ProgressReportTimer(
                        interval=self._option.report_interval)
                # download
                for data in response.iter_content(
                        chunk_size=self._option.chunk_size):
                    temp_file.write(data)
                    # update progress
                    progress.update(len(data))
                    if progress_timer.check():
                        reporter.progress(progress=progress.report())
            # move file
            with _move_file_lock:
                save_path = self._path
                i = 0
                while save_path.exists():
                    save_path = self._path.with_name(
                            '{0.stem}_{1}{0.suffix}'.format(self._path, i))
                    i += 1
                shutil.move(temp_file_path.as_posix(), save_path.as_posix())
            # chmod
            if self._option.file_permission is not None:
                save_path.chmod(self._option.file_permission)
            # finish report
            reporter.finish(
                    saved_path=save_path,
                    progress=progress.report())
        except (DownloadException, requests.RequestException) as error:
            reporter.error(error=error)
            # remove temp file
            if temp_file_path is not None:
                if temp_file_path.exists():
                    temp_file_path.unlink()
