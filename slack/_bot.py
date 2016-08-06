# -*- coding: utf-8 -*-

import argparse
import logging
import pathlib
import time
from typing import Optional
from slackclient import SlackClient

class SlackBot:
    def __init__(
                self,
                option: argparse.Namespace = None,
                logger: logging.Logger = None) -> None:
        # option
        if option is None:
            option = _create_option_parser().parse_args()
        self._option = option
        # logger
        self._logger = (
                    logger
                    if logger is not None
                    else logging.getLogger(__name__))
        if self._option.log_level is not None:
            self._logger.setLevel(
                            self._option.log_level)
        self._logger.debug('option: {0}'.format(self._option))
        # Token
        self._token = _load_token(
                    self._option.token_file,
                    self._logger)
        if self._token is None:
            self._logger.error('load token: Failed')
        else:
            self._logger.debug('load token: Success')
        # Client
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

def _create_option_parser() -> argparse.ArgumentParser:
    root_parser = argparse.ArgumentParser(
                description= 'SlackBot')
    # SlackBot option
    _slackbot_option_parser(root_parser)
    return root_parser

def _slackbot_option_parser(
            root_parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser = root_parser.add_argument_group(
                title= 'SlackBot Options')
    # Token File
    parser.add_argument(
                '--token-file',
                dest= 'token_file',
                type= pathlib.Path,
                required= True,
                help= ('set the path to the file '
                       'that Slack Authentification token is written'))
    # Log Level
    parser.add_argument(
                '--log-level',
                dest= 'log_level',
                action= _LogLevelAction,
                choices= ('debug', 'info', 'warning', 'error', 'critical'),
                help= 'set the threshold for the logger')
    return parser

class _LogLevelAction(argparse.Action):
    def __call__(
                self,
                parser: argparse.ArgumentParser,
                namespace: argparse.Namespace,
                value: str,
                option_string: str = None) -> None:
        setattr(namespace, self.dest, getattr(logging, value.upper()))

def _load_token(
            token_file: pathlib.Path,
            logger: logging.Logger) -> Optional[str]:
    if not token_file.exists():
        logger.error('Token File<{0}> does not exist'
                    .format(token_file.as_posix()))
        return None
    else:
        with token_file.open() as file:
            token = file.read().strip()
        return token
