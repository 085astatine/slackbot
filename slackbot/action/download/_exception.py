# -*- coding: utf-8 -*-

from ._progress import ProgressReport


class DownloadException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def __str__(self) -> str:
        return self._message


class IncompleteDownloadError(DownloadException):
    def __init__(self, progress: ProgressReport) -> None:
        super().__init__(
            message='incomplete download {0}B/{1}B'.format(
                    progress.downloaded_size,
                    progress.file_size))
        self._progress = progress

    @property
    def progress(self) -> ProgressReport:
        return self._progress
