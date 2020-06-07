# -*- coding: utf-8 -*-

import pathlib
import re
import shutil
import tempfile
import threading
from typing import NamedTuple, Optional, TypeVar, TYPE_CHECKING
import requests
from ... import Option, OptionList
from ._exception import IncompleteDownloadError
from ._report import Reporter
from ._progress import Progress, ProgressReportTimer
if TYPE_CHECKING:
    import queue
    from ._report import Report


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


ReportInfo = TypeVar('ReportInfo')


_move_file_lock = threading.Lock()


def download(
        url: str,
        path: pathlib.Path,
        info: ReportInfo,
        report_queue: 'queue.Queue[Report[ReportInfo]]',
        option: Optional[ThreadOption] = None) -> None:
    thread = threading.Thread(
            target=lambda: _download(
                    url=url,
                    path=path,
                    info=info,
                    report_queue=report_queue,
                    option=option))
    thread.start()


def _download(
        url: str,
        path: pathlib.Path,
        info: ReportInfo,
        report_queue: 'queue.Queue[Report[ReportInfo]]',
        option: Optional[ThreadOption] = None) -> None:
    if option is None:
        option = ThreadOption.option_list(name='').parse()
    # reporter
    reporter = Reporter(
            info=info,
            report_queue=report_queue,
            url=url,
            path=path)
    # mkdir
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    # download
    temp_file_path: Optional[pathlib.Path] = None
    try:
        with tempfile.NamedTemporaryFile(
                mode='wb',
                delete=False,
                dir=path.parent.as_posix()) as temp_file:
            temp_file_path = pathlib.Path(temp_file.name)
            # streaming download
            response = requests.get(url, stream=True)
            # status code check
            response.raise_for_status()
            # progress
            progress = Progress(
                    file_size=(int(response.headers['Content-Length'])
                               if 'Content-Length' in response.headers
                               else None),
                    speedmeter_size=option.speedmeter_size)
            progress_timer = ProgressReportTimer(
                    interval=option.report_interval)
            # start report
            reporter.start(
                    temp_path=temp_file_path,
                    response=response,
                    progress=progress.report())
            # download
            for data in response.iter_content(
                    chunk_size=option.chunk_size):
                temp_file.write(data)
                # update progress
                progress.update(len(data))
                if progress_timer.check():
                    reporter.progress(progress=progress.report())
        # complete check
        if not progress.is_completed():
            raise IncompleteDownloadError(progress.report())
        # move file
        with _move_file_lock:
            save_path = path
            i = 0
            while save_path.exists():
                save_path = path.with_name(
                        '{0.stem}_{1}{0.suffix}'.format(path, i))
                i += 1
            shutil.move(temp_file_path.as_posix(), save_path.as_posix())
        # chmod
        if option.file_permission is not None:
            save_path.chmod(option.file_permission)
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
