# -*- coding: utf-8 -*-

import pathlib
import re
import shutil
import tempfile
import threading
from typing import Generic, List, NamedTuple, Optional, TypeVar, TYPE_CHECKING
import requests
from ... import Option, OptionList
from ._exception import DownloadCancelled, IncompleteDownloadError
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


class Controller:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._is_finished = False
        self._is_canceled = False

    def finish(self) -> None:
        with self._lock:
            self._is_finished = True

    def is_finished(self) -> bool:
        with self._lock:
            return self._is_finished

    def cancel(self) -> None:
        with self._lock:
            self._is_canceled = True

    def is_canceled(self) -> bool:
        with self._lock:
            return self._is_canceled


class ThreadGenerator(Generic[ReportInfo]):
    def __init__(
            self,
            report_queue: 'queue.Queue[Report[ReportInfo]]',
            option: Optional[ThreadOption] = None) -> None:
        self._option = option
        self._report_queue = report_queue
        self._controllers: List[Controller] = []

    def start(
            self,
            url: str,
            path: pathlib.Path,
            info: ReportInfo) -> None:
        self.cleanup()
        controller = download(
                url=url,
                path=path,
                info=info,
                report_queue=self._report_queue,
                option=self._option)
        self._controllers.append(controller)

    def cleanup(self) -> None:
        for controller in self._controllers[:]:
            if controller.is_finished():
                self._controllers.remove(controller)

    def cancel(self) -> None:
        self.cleanup()
        for controller in self._controllers:
            controller.cancel()


def download(
        url: str,
        path: pathlib.Path,
        info: ReportInfo,
        report_queue: 'queue.Queue[Report[ReportInfo]]',
        option: Optional[ThreadOption] = None) -> Controller:
    controller = Controller()
    thread = threading.Thread(
            target=lambda: _download(
                    url=url,
                    path=path,
                    info=info,
                    report_queue=report_queue,
                    option=option,
                    controller=controller))
    thread.start()
    return controller


def _download(
        url: str,
        path: pathlib.Path,
        info: ReportInfo,
        report_queue: 'queue.Queue[Report[ReportInfo]]',
        *,
        option: Optional[ThreadOption] = None,
        controller: Optional[Controller] = None) -> None:
    option = option or ThreadOption.option_list(name='').parse()
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
                # check if cancelled
                if controller is not None and controller.is_canceled():
                    raise DownloadCancelled(progress.report())
        # complete check
        if not progress.is_completed():
            raise IncompleteDownloadError(progress.report())
        # move file
        save_path = _move_file(temp_file_path, path)
        temp_file_path = None
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
        if temp_file_path is not None and temp_file_path.exists():
            temp_file_path.unlink()
    finally:
        if controller:
            controller.finish()


_move_file_lock = threading.Lock()


def _move_file(
        source: pathlib.Path,
        destination: pathlib.Path) -> pathlib.Path:
    with _move_file_lock:
        path = destination
        i = 0
        while path.exists():
            path = source.with_name(
                    '{0.stem}_{1}{0.suffix}'.format(destination, i))
            i += 1
        shutil.move(source.as_posix(), path.as_posix())
    return path
