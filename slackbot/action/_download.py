# -*- coding: utf-8


import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from .. import Action, Option


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
