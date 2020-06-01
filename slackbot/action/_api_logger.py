# -*- coding: utf-8 -*-

import enum
import logging
import pprint
from typing import Callable, NamedTuple, Optional, Tuple
from .. import Action, Option, OptionList


class Mode(enum.Enum):
    raw = enum.auto()
    pprint = enum.auto()


class APILoggerOption(NamedTuple):
    mode: Mode
    event_list: Tuple[str, ...]

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
             Option('event_list',
                    action=lambda x: x if x is not None else [],
                    default=None,
                    help='event list for log output')],
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

    def register(self) -> None:
        for event in self._option.event_list:
            self.register_callback(
                    event=event,
                    callback=self._logging_callback(event=event))

    @staticmethod
    def option_list(name: str) -> OptionList[APILoggerOption]:
        return APILoggerOption.option_list(name)

    def _logging_callback(self, event: str) -> Callable:
        async def callback(**payload) -> None:
            data = payload['data']
            # raw
            if self.option.mode is Mode.raw:
                self._logger.info('event \'%s\': %r', event, data)
            # pprint
            elif self.option.mode is Mode.pprint:
                self._logger.info(
                        'event \'%s\': %s',
                        event,
                        '\n{0}'.format(pprint.pformat(data, indent=2)))
        return callback
