# -*- coding: utf-8 -*-

import collections
import datetime
import logging
import pathlib
import re
import shutil
import tempfile
import threading
import time
from typing import Deque, NamedTuple, Optional, Union
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


class DownloadProgress:
    def __init__(
            self,
            file_size: Optional[int],
            speedmeter_size: int) -> None:
        self._start_time = time.perf_counter()
        self._latest_time = self._start_time
        self._file_size = file_size
        self._downloaded_size = 0
        self._speedmeter = SpeedMeter(speedmeter_size)

    def update(self, size: int) -> None:
        self._downloaded_size += size
        self._latest_time = time.perf_counter()
        self._speedmeter.push(self._downloaded_size)

    @property
    def file_size(self) -> Optional[int]:
        return self._file_size

    @property
    def downloaded_size(self) -> int:
        return self._downloaded_size

    @property
    def remaining_size(self) -> Optional[int]:
        if self.file_size is not None:
            return self.file_size - self.downloaded_size
        else:
            return None

    @property
    def progress_rate(self) -> Optional[float]:
        if (self.file_size is not None) and (self.file_size > 0):
            return self.downloaded_size / self.file_size
        else:
            return None

    @property
    def elapsed_time(self) -> float:
        return self._latest_time - self._start_time

    @property
    def download_speed(self) -> Optional[float]:
        return self._speedmeter.speed()

    @property
    def average_download_speed(self) -> Optional[float]:
        if self.elapsed_time > 0:
            return self.downloaded_size / self.elapsed_time
        else:
            return None

    @property
    def remaining_time(self) -> Optional[float]:
        if self.file_size is None:
            return None
        elif (self.download_speed is None
              or self.remaining_size is None
              or self.download_speed <= 0.0):
            return None
        else:
            return self.remaining_size / self.download_speed

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


class DownloadException(Exception):
    def __init__(self, response: requests.models.Response) -> None:
        self._response = response

    def __str__(self) -> str:
        return 'status code [{0}]'.format(self._response.status_code)


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

    def _receive_progress(self, progress: DownloadProgress) -> None:
        format_bytes = DownloadProgress.format_bytes
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
                    format_bytes(progress.download_speed)))
        # elapsed time
        message.append('in {0}'.format(
                    str(datetime.timedelta(seconds=progress.elapsed_time))))
        # output to logger
        self._logger.debug('[{0}] progress: {1}'.format(
                    self._path.name,
                    ' '.join(message)))

    def _receive_finish(
                self,
                progress: DownloadProgress,
                save_path: pathlib.Path) -> None:
        format_bytes = DownloadProgress.format_bytes
        message = []
        if save_path == self._path:
            message.append('[{0}]:finish'.format(self._path.name))
        else:
            message.append('[{0}] -> [{1}]:finish'.format(
                        self._path.name,
                        save_path.name))
        message.append('{0} ({1}/s) in {2}'.format(
                    format_bytes(progress.downloaded_size),
                    format_bytes(progress.average_download_speed),
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


class DownloadThread(threading.Thread):
    def __init__(
                self,
                observer: DownloadObserver,
                path: pathlib.Path,
                url: str,
                option: DownloadThreadOption) -> None:
        threading.Thread.__init__(self)
        self._observer = observer
        self._path = path
        self._url = url
        self._option = option

    def run(self) -> None:
        # mkdir
        if not self._path.parent.exists():
            self._path.parent.mkdir(parents=True)
        # download
        with tempfile.NamedTemporaryFile(
                        mode='wb',
                        delete=False,
                        dir=self._path.parent.as_posix()) as temp_file:
            temp_file_path = pathlib.Path(temp_file.name)
            # initialize time
            start_time = time.perf_counter()
            present_time = start_time
            report_time = start_time
            try:
                # streaming download
                response = requests.get(self._url, stream=True)
                # status code check
                if ((response.status_code // 100 == 4)
                        or (response.status_code // 100 == 5)):
                    raise DownloadException(response)
                # start report
                self._observer._receive_start(
                            temp_file_path,
                            response)
                # file size
                content_length = response.headers.get('Content-Length', '')
                file_size = (int(content_length)
                             if content_length.isdigit()
                             else None)
                # initialize progress
                progress = DownloadProgress(
                        file_size,
                        self._option.speedmeter_size)
                # download
                for data in response.iter_content(
                        chunk_size=self._option.chunk_size):
                    temp_file.write(data)
                    # update progress
                    progress.update(len(data))
                    # update time
                    present_time = time.perf_counter()
                    # progress report
                    if (present_time - report_time
                            > self._option.report_interval):
                        # progress report
                        self._observer._receive_progress(progress)
                        # update report time
                        report_time = present_time
            except (DownloadException, requests.RequestException) as error:
                self._observer._receive_error(error)
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
        self._observer._receive_finish(
                    progress,
                    save_path)
