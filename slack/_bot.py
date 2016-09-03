# -*- coding: utf-8 -*-

import argparse
import logging
import pathlib
import pprint
import time
from typing import Dict, List, Optional, Tuple, Union
import slackclient
from ._team import Team, Channel, ChannelList, Member, MemberList

class SlackBot:
    def __init__(
                self,
                action_list: Dict[str, type] = None,
                option: argparse.Namespace = None,
                logger: logging.Logger = None) -> None:
        if action_list is None:
            action_list = {}
        # option
        if option is None:
            option = _create_option_parser(action_list).parse_args()
        self._option = option
        # logger
        self._logger = (
                    logger
                    if logger is not None
                    else logging.getLogger(__name__))
        # Action List
        self._action_list = {}# type: Dict[str, SlackBotAction]
        for key, action in action_list.items():
            self._action_list[key] = action(
                        key,
                        logger= self._logger.getChild(key),
                        option= self._option)
        assert all(isinstance(action, SlackBotAction)
                    for action in self._action_list.values())
        # set LogLevel
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
        self._client = slackclient.SlackClient(self._token)
        for action in self._action_list.values():
            action.set_client(self._client)
        # Team
        self._team = None # type: Team
    
    def run(self) -> None:
        self.update_team()
        if self._client.rtm_connect():
            self._logger.info('Connects to the RTM Websocket: Success')
            while True:
                data = self._client.rtm_read()
                for action in self._action_list.values():
                    action.action(data)
                time.sleep(self._option.wait)
        else:
            self._logger.error('Connects to the RTM WebSocket: Failed')
    
    def update_team(self) -> None:
        # API: auth.test
        api_auth_test = _api_call(self, 'auth.test')
        if api_auth_test is None:
            return
        team_id = api_auth_test['team_id']
        team_name = api_auth_test['team']
        user_id = api_auth_test['user_id']
        self._logger.debug('Team \"{0}\" (id: {1})'.format(team_name, team_id))
        # API: users.list
        api_users_list = _api_call(self, 'users.list')
        if api_users_list is None:
            return
        member_list = MemberList(tuple(
                    Member(member_data)
                    for member_data in api_users_list['members']
                    if not member_data['deleted']))
        self._logger.debug('\n{0}'.format(member_list.dump()))
        # API: channels.list
        api_channels_list = _api_call(self, 'channels.list')
        if api_channels_list is None:
            return
        channel_list = ChannelList(tuple(
                    Channel(channel_data, member_list)
                    for channel_data in api_channels_list['channels']
                    if not channel_data['is_archived']))
        self._logger.debug('\n{0}'.format(channel_list.dump()))
        # update Team
        self._team = Team(
                    team_id,
                    team_name,
                    member_list,
                    channel_list,
                    user_id)
        for action in self._action_list.values():
            action.set_team(self._team)
    
    def get_action(self, key: str) -> Optional['SlackBotAction']:
        return self._action_list.get(key, None)

class SlackBotAction:
    def __init__(
                self,
                name: str,
                logger: logging.Logger) -> None:
        self._logger = logger
        self._name = name
        self._client = None # type: slackclient._client.SlackClient
        self._team = None # type: Team
    
    @property
    def name(self) -> str:
        return self._name
    
    def action(self, api_list: List[dict]) -> None:
        pass
    
    def _api_call(
                self,
                method: str,
                **kwargs) -> Optional[dict]:
        return _api_call(self, method, **kwargs)
    
    def set_client(
                self,
                client: slackclient._client.SlackClient) -> None:
        self._client = client
    
    def set_team(
                self,
                team: Team) -> None:
        self._team = team
    
    @staticmethod
    def option_parser(
                name: str,
                root_parser: argparse.ArgumentParser) \
                -> argparse.ArgumentParser:
        return root_parser

def _api_call(
            self: Union[SlackBot, SlackBotAction],
            method: str,
            **kwargs) -> Optional[dict]:
    self._logger.info('call API \"{0}\"'.format(method))
    if len(kwargs) != 0:
        self._logger.debug('Argument\n{0}'.format(
                    pprint.pformat(kwargs, indent= 2)))
    data = self._client.api_call(method, **kwargs)
    self._logger.debug('call API \"{0}\": Result\n{1}'.format(
                method,
                pprint.pformat(data, indent= 2)))
    if not data.get('ok'):
        self._logger.error('call API \"{0}\": Error \"{1}\"'.format(
                    method,
                    data.get('error')))
        return None
    else:
        return data


def _create_option_parser(
            action_list: Dict[str, type]) -> argparse.ArgumentParser:
    root_parser = argparse.ArgumentParser(
                description= 'SlackBot')
    # SlackBot option
    _slackbot_option_parser(root_parser)
    # Action List
    for key in sorted(action_list.keys()):
        action_list[key].option_parser(key, root_parser)
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
                choices= _LogLevelAction.choices(),
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
    
    @staticmethod
    def choices() -> Tuple[str, ...]:
        return ('debug', 'info', 'warning', 'error', 'critical')

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
