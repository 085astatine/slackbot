# -*- coding: utf-8 -*-

import collections
import datetime
import logging
import pathlib
import shutil
import tempfile
import threading
import time
from typing import Deque, Optional, Tuple, Union
import requests


class DownloadProgress(object):
    def __init__(
                self,
                file_size: Optional[int],
                downloaded_size: int,
                start_time: float,
                present_time: float,
                download_speed: Optional[float]) -> None:
        self._file_size = file_size
        self._downloaded_size = downloaded_size
        self._start_time = start_time
        self._present_time = present_time
        self._download_speed = download_speed

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
        return self._present_time - self._start_time

    @property
    def download_speed(self) -> Optional[float]:
        return self._download_speed

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
        elif self.download_speed is None or self.download_speed <= 0.0:
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


class DownloadObserver(object):
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

    def start(self, **kwargs) -> None:
        thread = DownloadThread(
                    observer=self,
                    path=self._path,
                    url=self._url,
                    **kwargs)
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
                chunk_size: int = 1024,
                report_interval: float = 5.0,
                speedmeter_size: int = 100,
                permission: Optional[int] = None) -> None:
        threading.Thread.__init__(self)
        self._observer = observer
        self._path = path
        self._url = url
        self._chunk_size = chunk_size
        self._report_interval = report_interval
        self._speedmeter_size = speedmeter_size
        self._permission = permission

    def run(self) -> None:
        with tempfile.NamedTemporaryFile(
                        mode='wb',
                        delete=False,
                        dir=self._path.parent.as_posix()) as temp_file:
            temp_file_path = pathlib.Path(temp_file.name)
            # initialize parameter
            file_size: Optional[int] = None
            downloaded_size = 0
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
                # initialize speed meter
                speedmeter: Deque[Tuple[float, float]] = collections.deque(
                            maxlen=self._speedmeter_size)
                speedmeter.append((downloaded_size, present_time))
                # download
                for data in response.iter_content(chunk_size=self._chunk_size):
                    temp_file.write(data)
                    downloaded_size += len(data)
                    # update time
                    present_time = time.perf_counter()
                    # update speedmeter
                    speedmeter.append((downloaded_size, present_time))
                    # progress report
                    if present_time - report_time > self._report_interval:
                        # download speed
                        download_speed = (
                                (speedmeter[-1][0] - speedmeter[0][0])
                                / (speedmeter[-1][1] - speedmeter[0][1])
                                if speedmeter[-1][1] != speedmeter[0][1]
                                else None)
                        # progress report
                        progress = DownloadProgress(
                                    file_size=file_size,
                                    downloaded_size=downloaded_size,
                                    start_time=start_time,
                                    present_time=present_time,
                                    download_speed=download_speed)
                        self._observer._receive_progress(progress)
                        # update report time
                        report_time = present_time
            except (DownloadException, requests.RequestException) as error:
                self._observer._receive_error(error)
                temp_file_path.unlink()
                return
        # move file
        with _move_file_lock:
            if not self._path.parent.exists():
                self._path.parent.mkdir(parents=True)
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
        if self._permission is not None:
            save_path.chmod(self._permission)
        # finish report
        progress = DownloadProgress(
                    file_size=file_size,
                    downloaded_size=downloaded_size,
                    start_time=start_time,
                    present_time=time.perf_counter(),
                    download_speed=None)
        self._observer._receive_finish(
                    progress,
                    save_path)
