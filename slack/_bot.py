# -*- coding: utf-8 -*-

import argparse
import logging
import pathlib
import pprint
import time
from typing import Optional
from slackclient import SlackClient
from ._api import Channel, ChannelList, Member, MemberList

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
        self._member_list = MemberList()
        self._channel_list = ChannelList()
    
    def run(self) -> None:
        if self._client.rtm_connect():
            self._logger.info('Connects to the RTM Websocket: Success')
            while True:
                data = self._client.rtm_read()
                print(data)
                time.sleep(self._option.wait)
        else:
            self._logger.error('Connects to the RTM WebSocket: Failed')
    
    def update_member_list(self):
        self._logger.info('call API \"users.list\"')
        data = self._client.api_call('users.list')
        self._logger.debug(
                    'call API \"users.list\": Result\n{0}'
                    .format(pprint.pformat(data, indent= 2)))
        if not data.get('ok'):
            self._logger.error(
                        'call API \"users.list\": Error \"{0}\"'
                        .format(data.get('error')))
            return
        self._member_list = MemberList(tuple(
                    Member(member_data)
                    for member_data in data['members']
                    if not member_data['deleted']))
        self._logger.debug('\n{0}'.format(self._member_list.dump()))
    
    def update_channel_list(self):
        self._logger.info('call API \"channels.list\"')
        data = self._client.api_call('channels.list')
        self._logger.debug(
                    'call API \"channels.list\": Result\n{0}'
                    .format(pprint.pformat(data, indent= 2)))
        if not data.get('ok'):
            self._logger.error(
                        'call API \"channels.list\": Error \"{0}\"'
                        .format(data.get('error')))
            return
        self._channel_list = ChannelList(tuple(
                    Channel(channel_data, self._member_list)
                    for channel_data in data['channels']
                    if not channel_data['is_archived']))
        self._logger.debug('\n{0}'.format(self._channel_list.dump()))

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
    # Wait Time
    parser.add_argument(
                '--wait',
                dest= 'wait',
                metavar= 'SECONDS',
                type= float,
                default= 1.0,
                help= ('set seconds between reading from'
                       'Real Time Messaging WebSocket stream'))
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
