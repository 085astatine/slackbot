# -*- cpding: utf-8 -*-

import datetime
import logging
from typing import Any, List, NamedTuple, Optional, Tuple, Union
from .. import Action, Option, OptionError, OptionList


class ChannelOption:
    def __init__(self, name: str, period: Union[float, int]) -> None:
        assert(isinstance(name, str))
        assert(isinstance(period, (float, int)))
        self._name = name
        self._period = datetime.timedelta(hours=period)

    def __repr__(self) -> str:
        return "{0}.{1}(name={2}, period={3})".format(
                self.__class__.__module__,
                self.__class__.__name__,
                repr(self._name),
                repr(self._period))

    @property
    def name(self) -> str:
        return self._name

    @property
    def period(self) -> datetime.timedelta:
        return self._period


class ClearHistoryOption(NamedTuple):
    sleep: float
    api_interval: float
    channels: Tuple[ChannelOption, ...]

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['ClearHistoryOption']:
        def parse_channel(data: Any) -> Tuple[ChannelOption, ...]:
            result: List[ChannelOption] = []
            if not (isinstance(data, list)
                    and all(map(lambda x: isinstance(x, dict), data))):
                raise OptionError(
                    'could not convert to ChannelOption\'s list: \'{0}\''
                    .format(data))
            for channel in data:
                try:
                    result.append(ChannelOption(**channel))
                except (AssertionError, TypeError):
                    raise OptionError(
                            'could not convert to ChannelOption: \'{0}\''
                            .format(channel))
            return tuple(result)

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
                        help='slack api execution interval (seconds)'),
                 Option('channels',
                        sample=[{'name': 'CHANNEL_NAME', 'period': 24}],
                        action=parse_channel,
                        help='target channels')],
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
