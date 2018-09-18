# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional, Dict, List, Optional, Tuple
from ._client import Client
from ._config import Option
from ._team import Team


class Action(object):
    def __init__(self,
                 name: str,
                 config: Any,
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
    def config(self) -> Any:
        return self._config

    @property
    def team(self) -> Team:
        return Team(key=self._key)

    @staticmethod
    def option_list() -> Tuple[Option, ...]:
        return tuple()


def escape_text(string: str) -> str:
    return (string.replace('&', '&amp;')
                  .replace('>', '&gt;')
                  .replace('<', '&lt;'))


def unescape_text(string: str) -> str:
    return (string.replace('&amp;', '&')
                  .replace('&gt;', '>')
                  .replace('&lt;', '<'))
