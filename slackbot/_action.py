# -*- coding: utf-8 -*-

import logging
from typing import (
        Any, Dict, Generic, List, NamedTuple, Optional, Tuple, TypeVar)
from ._client import Client
from ._config import OptionList
from ._team import Team


OptionType = TypeVar('OptionType')


class NoneOption(NamedTuple):
    pass


class Action(Generic[OptionType]):
    def __init__(self,
                 name: str,
                 config: OptionType,
                 key: Optional[str] = None,
                 logger: Optional[logging.Logger] = None) -> None:
        # logger
        if not hasattr(self, '_logger'):
            self._logger = logger or logging.getLogger(__name__)
        else:
            assert isinstance(self._logger, logging.Logger)
        # parameter
        self._name = name
        self._config = config
        self._key = key
        self._client = Client(key=self._key, logger=self._logger)

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        pass

    def api_call(self, method: str, **kwargs):
        return self._client.api_call(method, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> OptionType:
        return self._config

    @property
    def team(self) -> Team:
        return Team(key=self._key)

    @staticmethod
    def option_list(name: str) -> OptionList:
        return OptionList(NoneOption, name, [])


def escape_text(string: str) -> str:
    return (string.replace('&', '&amp;')
                  .replace('>', '&gt;')
                  .replace('<', '&lt;'))


def unescape_text(string: str) -> str:
    return (string.replace('&amp;', '&')
                  .replace('&gt;', '>')
                  .replace('&lt;', '<'))
