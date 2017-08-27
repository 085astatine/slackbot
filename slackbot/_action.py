# -*- coding: utf-8 -*-


import logging
from typing import Any, Optional, Dict, List, Optional, Tuple, TYPE_CHECKING
import slackclient
from ._config import Option
if TYPE_CHECKING:
    from ._info import Info


class Action(object):
    def __init__(self,
                 name: str,
                 config: Any,
                 logger: Optional[logging.Logger] = None) -> None:
        self._name = name
        self._config = config
        self._client: Optional[slackclient.SlackClient] = None
        self._info: Optional['Info'] = None
        if not hasattr(self, '_logger'):
            self._logger = (logger
                            if logger is not None
                            else logging.getLogger(__name__))
        else:
            assert isinstance(self._logger, logging.Logger)

    def setup(self, client: slackclient.SlackClient, info: 'Info') -> None:
        self._client = client
        self._info = info

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        pass

    def api_call(self, method: str, **kwargs):
        self._logger.debug("call API '{0}': {1}".format(method, kwargs))
        result = self._client.api_call(method, **kwargs)
        self._logger.log(
                    (logging.DEBUG
                        if result.get('ok', False)
                        else logging.ERROR),
                    'result: {0}'.format(result))
        return result

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> Any:
        return self._config

    @property
    def info(self) -> 'Info':
        return self._info

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
