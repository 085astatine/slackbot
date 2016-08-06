# -*- coding: utf-8 -*-

import logging
import time
from slackclient import SlackClient

class SlackBot:
    def __init__(
                self,
                token: str,
                logger: logging.Logger = None) -> None:
        # logger
        self._logger = (
                    logger
                    if logger is not None
                    else logging.getLogger(__name__))
        self._token = token
        self._client = SlackClient(self._token)
    
    def run(self) -> None:
        if self._client.rtm_connect():
            self._logger.info('Connects to the RTM Websocket: Success')
            while True:
                data = self._client.rtm_read()
                print(data)
                time.sleep(1)
        else:
            self._logger.error('Connects to the RTM WebSocket: Failed')
