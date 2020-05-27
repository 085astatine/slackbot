# -*- cpding: utf-8 -*-

import logging
from typing import NamedTuple, Optional
from .. import Action, Option, OptionList


class ClearHistoryOption(NamedTuple):
    sleep: float
    api_interval: float

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['ClearHistoryOption']:
        return OptionList(
                ClearHistoryOption,
                name,
                [Option('sleep',
                        type=float,
                        default=float(24 * 60 * 60),
                        help='clear execution interval of (seconds)'),
                 Option('api_interval',
                        type=float,
                        default=1.0,
                        help='slack api execution interval (seconds)')],
                help=help)


class ClearHistory(Action[ClearHistoryOption]):
    def __init__(
            self,
            name: str,
            option: ClearHistoryOption,
            logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                name,
                option,
                logger=logger or logging.getLogger(__name__))

    @staticmethod
    def option_list(name: str) -> OptionList[ClearHistoryOption]:
        return ClearHistoryOption.option_list(name)
