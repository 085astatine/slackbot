# -*- coding: utf-8 -*-

import pathlib
import re
import shutil
import tempfile
import threading
from typing import Generic, NamedTuple, Optional, TypeVar, TYPE_CHECKING
import requests
from ... import Option, OptionList
from ._exception import IncompleteDownloadError
from ._report import Reporter
from ._progress import Progress, ProgressReportTimer
if TYPE_CHECKING:
    import queue
    from ._report import Report


ReportInfo = TypeVar('ReportInfo')


class ThreadOption(NamedTuple):
    chunk_size: int
    report_interval: float
    speedmeter_size: int
    file_permission: Optional[int]

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['ThreadOption']:
        # parse permission (format 0oXXX)
        def read_permission(value: str) -> Optional[int]:
            match = re.match('0o(?P<permission>[0-7]{3})', value)
            if match:
                return int(match.group('permission'), base=8)
            return None

        return OptionList(
            ThreadOption,
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


class Thread(threading.Thread, Generic[ReportInfo]):
    _move_file_lock = threading.Lock()

    def __init__(
                self,
                info: ReportInfo,
                report_queue: 'queue.Queue[Report[ReportInfo]]',
                path: pathlib.Path,
                url: str,
                option: ThreadOption) -> None:
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
                # progress
                progress = Progress(
                        file_size=(int(response.headers['Content-Length'])
                                   if 'Content-Length' in response.headers
                                   else None),
                        speedmeter_size=self._option.speedmeter_size)
                progress_timer = ProgressReportTimer(
                        interval=self._option.report_interval)
                # start report
                reporter.start(
                        temp_path=temp_file_path,
                        response=response,
                        progress=progress.report())
                # download
                for data in response.iter_content(
                        chunk_size=self._option.chunk_size):
                    temp_file.write(data)
                    # update progress
                    progress.update(len(data))
                    if progress_timer.check():
                        reporter.progress(progress=progress.report())
            # complete check
            if not progress.is_completed():
                raise IncompleteDownloadError(progress.report())
            # move file
            with self._move_file_lock:
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
        except Exception as error:
            reporter.error(error=error)
            # remove temp file
            if temp_file_path is not None:
                if temp_file_path.exists():
                    temp_file_path.unlink()
