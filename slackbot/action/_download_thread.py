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
    def option_list(name: str, help: str = '') -> OptionList:
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

    def update(self, received_size: int) -> None:
        self._downloaded_size += received_size
        self._latest_time = time.perf_counter()
        self._speedmeter.push(self._downloaded_size)

    def report(self) -> ProgressReport:
        return ProgressReport(
                file_size=self._file_size,
                downloaded_size=self._downloaded_size,
                elapsed_time=self._latest_time - self._start_time,
                speed=self._speedmeter.speed())


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
            response_header: Optional[MutableMapping[str, str]],
            progress: ProgressReport,
            saved_path: Optional[pathlib.Path] = None,
            error: Optional[Exception] = None) -> None:
        self.type = type
        self.info = info
        self.url = url
        self.path = path
        self.temp_path = temp_path
        self.response_header = response_header
        self.progress = progress
        self.saved_path = saved_path
        self.error = error

    def __repr__(self) -> str:
        keys = ['type', 'info', 'url', 'path', 'temp_path', 'response_header',
                'progress', 'saved_path', 'error']
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
            report_queue: queue.Queue[DownloadReport[ReportInfo]],
            url: str,
            path: pathlib.Path,
            speedmeter_size: int,
            progress_report_interval: float) -> None:
        self._report_queue = report_queue
        # timer
        self._report_time = time.perf_counter()
        self._report_interval = progress_report_interval
        # report parameter
        self._info = info
        self._url = url
        self._path = path
        self._temp_path: Optional[pathlib.Path] = None
        self._response_header: Optional[MutableMapping[str, str]] = None
        self._saved_path: Optional[pathlib.Path] = None
        self._error: Optional[Exception] = None
        # progress
        self._speedmeter_size = speedmeter_size
        self._progress = Progress(None, self._speedmeter_size)

    def start(
            self,
            temp_path: pathlib.Path,
            response_header: MutableMapping[str, str]) -> None:
        self._temp_path = temp_path
        self._response_header = response_header
        # progress
        content_length = response_header.get('Content-Length', '')
        file_size = int(content_length) if content_length.isdigit() else None
        self._progress = Progress(file_size, self._speedmeter_size)
        # start report
        self._report_time = time.perf_counter()
        self.report(DownloadReportType.START)

    def update_progress(self, received_size: int) -> None:
        # update progress
        self._progress.update(received_size)
        # report
        current_time = time.perf_counter()
        if current_time - self._report_time > self._report_interval:
            self._report_time = current_time
            self.report(DownloadReportType.PROGRESS)

    def finish(self, saved_path: pathlib.Path) -> None:
        self._saved_path = saved_path
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
                response_header=self._response_header,
                progress=self._progress.report(),
                saved_path=self._saved_path,
                error=self._error)

    def report(self, type: DownloadReportType) -> None:
        self._report_queue.put(self.create_report(type))


class DownloadObserver:
    def __init__(
                self,
                path: Union[str, pathlib.Path],
                url: str,
                logger: Optional[logging.Logger] = None) -> None:
        self._path = (path
                      if isinstance(path, pathlib.Path)
                      else pathlib.Path(path))
        self._url = url
        if not hasattr(self, '_logger'):
            self._logger = logger or logging.getLogger(__name__)
        else:
            assert isinstance(self._logger, logging.Logger)
        self._is_finished = False
        self._lock = threading.Lock()

    def start(self, option: DownloadThreadOption) -> None:
        thread = DownloadThread(
                    observer=self,
                    path=self._path,
                    url=self._url,
                    option=option)
        thread.start()

    def is_finished(self) -> bool:
        with self._lock:
            return self._is_finished

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def url(self) -> str:
        return self._url

    def _receive_start(
                self,
                temp_file_path: pathlib.Path,
                response: requests.models.Response) -> None:
        self._logger.info('[{0}] url: {1}'.format(
                    self._path.name,
                    response.url))
        self._logger.info('[{0}] file size: {1}'.format(
                    self._path.name,
                    response.headers.get('Content-Length')))
        self._logger.debug('[{0}] temp file: {1}'.format(
                    self._path.name,
                    temp_file_path.as_posix()))
        self._logger.debug('[{0}] header: {1}'.format(
                    self._path.name,
                    response.headers))

    def _receive_progress(self, progress: ProgressReport) -> None:
        format_bytes = ProgressReport.format_bytes
        message = []
        # progress rate
        if progress.file_size is not None:
            message.append('{0}/{1} ({2:.2%})'.format(
                    format_bytes(progress.downloaded_size),
                    format_bytes(progress.file_size),
                    progress.progress_rate))
        else:
            message.append('{0}/{1}'.format(
                    format_bytes(progress.downloaded_size),
                    format_bytes(progress.file_size)))
        # speed
        message.append('{0}/s'.format(
                    format_bytes(progress.speed)))
        # elapsed time
        message.append('in {0}'.format(
                    str(datetime.timedelta(seconds=progress.elapsed_time))))
        # output to logger
        self._logger.debug('[{0}] progress: {1}'.format(
                    self._path.name,
                    ' '.join(message)))

    def _receive_finish(
                self,
                progress: ProgressReport,
                save_path: pathlib.Path) -> None:
        format_bytes = ProgressReport.format_bytes
        message = []
        if save_path == self._path:
            message.append('[{0}]:finish'.format(self._path.name))
        else:
            message.append('[{0}] -> [{1}]:finish'.format(
                        self._path.name,
                        save_path.name))
        message.append('{0} ({1}/s) in {2}'.format(
                    format_bytes(progress.downloaded_size),
                    format_bytes(progress.average_speed),
                    str(datetime.timedelta(seconds=progress.elapsed_time))))
        self._logger.info(' '.join(message))
        with self._lock:
            self._is_finished = True

    def _receive_error(self, error: Exception) -> None:
        self._logger.error('[{0}] {1}: {2}'.format(
                    self._path.name,
                    error.__class__.__name__,
                    str(error)))
        with self._lock:
            self._is_finished = True


_move_file_lock = threading.Lock()


class DownloadThread(threading.Thread, Generic[ReportInfo]):
    def __init__(
                self,
                info: ReportInfo,
                report_queue: queue.Queue[DownloadReport[ReportInfo]],
                path: pathlib.Path,
                url: str,
                option: DownloadThreadOption) -> None:
        threading.Thread.__init__(self)
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
                path=self._path,
                speedmeter_size=self._option.speedmeter_size,
                progress_report_interval=self._option.report_interval)
        # mkdir
        if not self._path.parent.exists():
            self._path.parent.mkdir(parents=True)
        # download
        with tempfile.NamedTemporaryFile(
                        mode='wb',
                        delete=False,
                        dir=self._path.parent.as_posix()) as temp_file:
            temp_file_path = pathlib.Path(temp_file.name)
            try:
                # streaming download
                response = requests.get(self._url, stream=True)
                # status code check
                if ((response.status_code // 100 == 4)
                        or (response.status_code // 100 == 5)):
                    raise DownloadException(response)
                # start report
                reporter.start(
                        temp_path=temp_file_path,
                        response_header=response.headers)
                # download
                for data in response.iter_content(
                        chunk_size=self._option.chunk_size):
                    temp_file.write(data)
                    # update reporter
                    reporter.update_progress(len(data))
            except (DownloadException, requests.RequestException) as error:
                reporter.error(error=error)
                temp_file_path.unlink()
                return
        # move file
        with _move_file_lock:
            save_path = self._path
            if save_path.exists():
                index = 0
                while save_path.exists():
                    save_path = self._path.parent.joinpath(
                                    '{0.stem}_{1}{0.suffix}'
                                    .format(self._path, index))
                    index += 1
            shutil.move(temp_file_path.as_posix(), save_path.as_posix())
        # chmod
        if self._option.file_permission is not None:
            save_path.chmod(self._option.file_permission)
        # finish report
        reporter.finish(saved_path=save_path)
