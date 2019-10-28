# -*- coding: utf-8 -*-

import logging
from typing import (
        Any, Callable, Dict, Generic, List, NamedTuple, Optional, TypeVar)
import slack
from ._option import OptionList
from ._team import Team


OptionType = TypeVar('OptionType')


class NoneOption(NamedTuple):
    pass


class Action(Generic[OptionType]):
    def __init__(self,
                 name: str,
                 option: OptionType,
                 logger: Optional[logging.Logger] = None) -> None:
        # logger
        if not hasattr(self, '_logger'):
            self._logger = logger or logging.getLogger(__name__)
        else:
            assert isinstance(self._logger, logging.Logger)
        # parameter
        self._name = name
        self._option = option
        self._team = Team()

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        pass

    def register(self) -> None:
        pass

    def update(self, client: slack.WebClient) -> None:
        pass

    def api_call(self, method: str, **kwargs):
        return self._client.api_call(method, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def option(self) -> OptionType:
        return self._option

    @property
    def team(self) -> Team:
        return self._team

    @staticmethod
    def option_list(name: str) -> OptionList:
        return OptionList(NoneOption, name, [])

    @classmethod
    def register_callback(
            cls,
            *,
            event: str,
            callback: Callable) -> None:
        slack.RTMClient.on(
                event=event,
                callback=callback)


def escape_text(string: str) -> str:
    return (string.replace('&', '&amp;')
                  .replace('>', '&gt;')
                  .replace('<', '&lt;'))


def unescape_text(string: str) -> str:
    return (string.replace('&amp;', '&')
                  .replace('&gt;', '>')
                  .replace('&lt;', '<'))
