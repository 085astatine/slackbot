# -*- coding: utf-8


import datetime
import logging
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple
import requests
from .. import Action, Option
from .._info import Channel
from ._download_thread import DownloadObserver, DownloadProgress


class DownloadReport(Action, DownloadObserver):
    def __init__(self,
                 path: pathlib.Path,
                 url: str,
                 channel: Channel,
                 logger: Optional[logging.Logger] = None) -> None:
        Action.__init__(
                    self,
                    None,
                    None,
                    (logger
                        if logger is not None
                        else logging.getLogger(__name__)))
        DownloadObserver.__init__(
                    self,
                    path,
                    url,
                    self._logger)
        self._channel = channel

    def _receive_start(
                self,
                temp_file_path: pathlib.Path,
                response: requests.models.Response) -> None:
        DownloadObserver._receive_start(self, temp_file_path, response)
        # post message
        file_size = (
                    int(response.headers.get('Content-Length'))
                    if response.headers.get('Content-Length', '').isdigit()
                    else None)
        message = '[{0}]:start <{1}> (size: {2})'.format(
                    self._path.name,
                    response.url,
                    DownloadProgress.format_bytes(file_size))
        self.api_call('chat.postMessage',
                      text=message,
                      channel=self._channel.id)

    def _receive_progress(self, progress: DownloadProgress) -> None:
        DownloadObserver._receive_progress(self, progress)
        # post message
        format_bytes = DownloadProgress.format_bytes
        message = []
        message.append('[{0}]:progress'.format(self._path.name))
        if progress.file_size is not None:
            message.append('{0}/{1} ({2:.2%})'.format(
                        format_bytes(progress.downloaded_size),
                        format_bytes(progress.file_size),
                        progress.progress_rate))
        else:
            message.append('{0}'.format(
                        format_bytes(progress.downloaded_size)))
        message.append('{0}/s'.format(
                    format_bytes(progress.download_speed)))
        message.append('in {0}'.format(
                    str(datetime.timedelta(seconds=progress.elapsed_time))))
        message.append('(remaining {0})'.format(
                    str(datetime.timedelta(seconds=progress.remaining_time))))
        self.api_call('chat.postMessage',
                      text=' '.join(message),
                      channel=self._channel.id)

    def _receive_finish(self, progress: DownloadProgress) -> None:
        DownloadObserver._receive_finish(self, progress)
        # post message
        format_bytes = DownloadProgress.format_bytes
        message = '[{0}]:finish {1} at {2}/s in {3}'.format(
                    self._path.name,
                    format_bytes(progress.downloaded_size),
                    format_bytes(progress.average_download_speed),
                    str(datetime.timedelta(seconds=progress.elapsed_time)))
        self.api_call('chat.postMessage',
                      text=message,
                      channel=self._channel.id)

    def _receive_error(self, error: Exception) -> None:
        DownloadObserver._receive_error(self, error)
        # post message
        message = '[{0}]:error {1}: {2}'.format(
                    self._path.name,
                    error.__class__.__name__,
                    str(error))
        self.api_call('chat.postMessage',
                      text=message,
                      channel=self._channel.id)


class Download(Action):
    def __init__(self,
                 name: str,
                 config: Any,
                 logger: Optional[logging.Logger] = None) -> None:
        Action.__init__(
                    self,
                    name,
                    config,
                    (logger
                        if logger is not None
                        else logging.getLogger(__name__)))
        self._process_list: List[DownloadReport] = []

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        for api in api_list:
            if api['type'] == 'message' and 'subtype' not in api:
                channel = self.info.channel_list.id_search(api['channel'])
                if channel is None or channel.name not in self.config.channel:
                    continue
                match = self.config.pattern.match(api['text'].strip())
                if match:
                    name = match.group('name')
                    url = match.group('url')
                    self._logger.info('name: {0}'.format(name))
                    self._logger.info('url: {0}'.format(url))
                    # create process
                    process = DownloadReport(
                                name,
                                url,
                                channel,
                                logger=self._logger.getChild('report'))
                    process.setup(
                                self._client,
                                self._info)
                    process.start(
                                report_interval=10.0)
                    self._process_list.append(process)
        # update process list
        finished_process_list = [
                    process for process in self._process_list
                    if process.is_finished()]
        for finished_process in finished_process_list:
            self._process_list.remove(finished_process)

    @staticmethod
    def option_list() -> Tuple[Option, ...]:
        return (
            Option('channel',
                   action=lambda x: [x] if isinstance(x, str) else x,
                   default=[],
                   help='target channel name (list or string)'),
            Option('pattern',
                   action=re.compile,
                   default=r'download\s+"(?P<name>.+)"\s+'
                           r'<(?P<url>https?://[\w/:%#\$&\?\(\)~\.=\+\-]+)'
                           r'(|\|[^>]+)>',
                   help=('regular expresion for working'
                         'which have simbolic groups named "name" & "url"')))
