# -*- coding: utf-8 -*-

import enum
import logging
import pprint
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
from .. import Action, Option, OptionList


class Mode(enum.Enum):
    raw = enum.auto()
    pprint = enum.auto()


class APILoggerOption(NamedTuple):
    mode: Mode
    ignore_reconnect_url: bool
    ignore_presence_change: bool
    ignore_user_typing: bool

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['APILoggerOption']:
        return OptionList(
            APILoggerOption,
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
                    help='ignore "user_typing" api')],
            help=help)


class APILogger(Action[APILoggerOption]):
    def __init__(
            self,
            name: str,
            option: APILoggerOption,
            logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                name,
                option,
                logger=logger or logging.getLogger(__name__))

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        for api in api_list:
            # ignore check
            if (self.option.ignore_reconnect_url
                    and api['type'] == 'reconnect_url'):
                continue
            if (self.option.ignore_presence_change
                    and api['type'] == 'presence_change'):
                continue
            if (self.option.ignore_user_typing
                    and api['type'] == 'user_typing'):
                continue
            # raw
            if self.option.mode is Mode.raw:
                self._logger.info(repr(api))
            # pprint
            elif self.option.mode is Mode.pprint:
                self._logger.info(
                        '\n{0}'.format(pprint.pformat(api, indent=2)))

    @staticmethod
    def option_list(name: str) -> OptionList[APILoggerOption]:
        return APILoggerOption.option_list(name)
