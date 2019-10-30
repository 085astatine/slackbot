# -*- coding: utf-8 -*-

import enum
import pathlib
from typing import (
        Generic, MutableMapping, Optional, TypeVar, Union, TYPE_CHECKING)
import requests
from ._progress import ProgressReport
if TYPE_CHECKING:
    import queue


ReportInfo = TypeVar('ReportInfo')


class ReportType(enum.Enum):
    START = enum.auto()
    PROGRESS = enum.auto()
    FINISH = enum.auto()
    ERROR = enum.auto()


class Report(Generic[ReportInfo]):
    def __init__(
            self,
            type: ReportType,
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
            report_queue: 'queue.Queue[Report[ReportInfo]]',
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
        self.report(ReportType.START)

    def progress(
            self,
            progress: ProgressReport) -> None:
        self._progress = progress
        # report
        self.report(ReportType.PROGRESS)

    def finish(
            self,
            saved_path: pathlib.Path,
            progress: ProgressReport) -> None:
        self._saved_path = saved_path
        self._progress = progress
        # report
        self.report(ReportType.FINISH)

    def error(self, error: Exception) -> None:
        self._error = error
        # report
        self.report(ReportType.ERROR)

    def create_report(
            self,
            type: ReportType) -> Report[ReportInfo]:
        return Report(
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

    def report(self, type: ReportType) -> None:
        self._report_queue.put(self.create_report(type))
