# -*- coding: utf-8 -*-

import logging
from typing import Any, Dict, List, Optional
import slackclient


_client: Dict[Optional[str], slackclient.SlackClient] = {}
_ref_count: Dict[Optional[str], int] = {}


class Client:
    def __init__(
            self,
            key: Optional[str] = None,
            timeout: Optional[float] = None,
            logger: Optional[logging.Logger] = None) -> None:
        self._key = key
        self._timeout = timeout
        self._logger = logger or logging.getLogger(__name__)
        # register client
        if self._key not in _client:
            _client[self._key] = None
            _ref_count[self._key] = 1
        else:
            _ref_count[self._key] += 1

    def __del__(self):
        _ref_count[self._key] -= 1
        if _ref_count[self._key] <= 0:
            del _client[self._key]
            del _ref_count[self._key]

    def setup(self, token: str) -> None:
        if _client[self._key] is None:
            _client[self._key] = slackclient.SlackClient(token)

    def api_call(self, method: str, **kwargs) -> Dict[str, Any]:
        if _client[self._key] is not None:
            self._logger.debug("call API '{0}': {1}".format(method, kwargs))
            result = _client[self._key].api_call(
                    method,
                    timeout=self._timeout,
                    **kwargs)
            self._logger.log(
                    logging.DEBUG if result.get('ok', False) else logging.INFO,
                    '{0} result: {1}'.format(method, result))
            return result
        else:
            return {}

    def rtm_connect(self, reconnect: bool = False) -> bool:
        if _client[self._key] is not None:
            return _client[self._key].rtm_connect(
                    with_team_state=False,
                    timeout=self._timeout)
        else:
            return False

    def rtm_read(self) -> List[Any]:
        if _client[self._key] is not None:
            return _client[self._key].rtm_read()
        else:
            return []

    def is_connected(self) -> bool:
        if _client[self._key] is not None:
            return _client[self._key].server.connected
        else:
            return False
