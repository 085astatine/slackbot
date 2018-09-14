# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional, Dict, List, Optional, Tuple, TYPE_CHECKING
from ._client import Client
from ._config import Option
if TYPE_CHECKING:
    from ._team import Team


class Action(object):
    def __init__(self,
                 name: str,
                 config: Any,
                 logger: Optional[logging.Logger] = None) -> None:
        # logger
        if not hasattr(self, '_logger'):
            self._logger = logger or logging.getLogger(__name__)
        else:
            assert isinstance(self._logger, logging.Logger)
        # parameter
        self._name = name
        self._config = config
        self._client: Client = Client(logger=self._logger)
        self._team: Optional['Team'] = None

    def setup(self, token: str, team: 'Team') -> None:
        self._client.setup(token)
        self._team = team

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
    def team(self) -> 'Team':
        return self._team

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
