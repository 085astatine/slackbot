# -*- coding: utf-8 -*-

import enum
import logging
import pprint
from typing import Any, Dict, List, Optional, Tuple
from .. import Action, Option, OptionList


class Mode(enum.Enum):
    raw = enum.auto()
    pprint = enum.auto()


class APILogger(Action):
    def __init__(
            self,
            name: str,
            config: Any,
            key: Optional[str] = None,
            logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                name,
                config,
                key=key,
                logger=logger or logging.getLogger(__name__))

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        for api in api_list:
            # ignore check
            if (self.config.ignore_reconnect_url
                    and api['type'] == 'reconnect_url'):
                continue
            if (self.config.ignore_presence_change
                    and api['type'] == 'presence_change'):
                continue
            if (self.config.ignore_user_typing
                    and api['type'] == 'user_typing'):
                continue
            # raw
            if self.config.mode is Mode.raw:
                self._logger.info(repr(api))
            # pprint
            elif self.config.mode is Mode.pprint:
                self._logger.info(
                        '\n{0}'.format(pprint.pformat(api, indent=2)))

    @staticmethod
    def option_list(name: str) -> OptionList:
        return OptionList(
            name,
            [Option('mode',
                    action=lambda mode: getattr(Mode, mode),
                    default='raw',
                    choices=[mode.name for mode in Mode],
                    help='output format'),
             Option('ignore_reconnect_url',
                    type=bool,
                    default=True,
                    help='ignore "reconnect_url" api'),
             Option('ignore_presence_change',
                    type=bool,
                    default=True,
                    help='ignore "presence_change" api'),
             Option('ignore_user_typing',
                    type=bool,
                    default=True,
                    help='ignore "user_typing" api')])
