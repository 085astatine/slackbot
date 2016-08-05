# -*- coding: utf-8 -*-

import time
from slackclient import SlackClient

class SlackBot:
    def __init__(
                self,
                token: str) -> None:
        self._token = token
        self._client = SlackClient(self._token)
    
    def run(self) -> None:
        if self._client.rtm_connect():
            while True:
                data = self._client.rtm_read()
                print(data)
                time.sleep(1)
        else:
            print('Connection Failed')
