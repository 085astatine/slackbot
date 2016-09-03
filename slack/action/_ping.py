# -*- coding: utf-8 -*-

import argparse
import logging
import re
from typing import List
from .._bot import SlackBotAction, _LogLevelAction

class Ping(SlackBotAction):
    def __init__(
                self,
                name: str,
                logger: logging.Logger,
                option: argparse.ArgumentParser) -> None:
        SlackBotAction.__init__(self, name, logger)
        # set Log Level
        log_level = getattr(option, '{0}.log_level'.format(self.name))
        if log_level is not None:
            self._logger.setLevel(log_level)
        # Setting
        self._keyword_text = getattr(option, '{0}.keyword'.format(self.name))
        self._reply_text = getattr(option, '{0}.reply'.format(self.name))
    
    def action(self, api_list: List[dict]) -> None:
        for api in api_list:
            if _is_target(self, api):
                self._logger.info('send Reply')
                _send_reply(self, api)
    
    @staticmethod
    def option_parser(
                name: str,
                root_parser: argparse.ArgumentParser) \
                -> argparse.ArgumentParser:
        parser = root_parser.add_argument_group(
                    title= '{0} Options'.format(name))
        # Log Level
        parser.add_argument(
                    '--{0}-log-level'.format(name),
                    dest= '{0}.log_level'.format(name),
                    action= _LogLevelAction,
                    choices= _LogLevelAction.choices(),
                    help= 'set the threshold for the logger')
        # Keyword Text
        parser.add_argument(
                    '--{0}-keyword'.format(name),
                    dest= '{0}.keyword'.format(name),
                    default= 'ping',
                    metavar= 'TEXT',
                    help= 'set the keyword to reply. default keyword is ping')
        # Replay Text
        parser.add_argument(
                    '--{0}-reply'.format(name),
                    dest= '{0}.reply'.format(name),
                    default= 'pong',
                    metavar= 'TEXT',
                    help= 'set the reply message. default message is pong')
        return root_parser

def _is_target(
            self: Ping,
            api: dict) -> bool:
    if api.get('type') == 'message':
        pattern = r'(<@(?P<to>.+)> +|)(?P<text>.+)'
        regex = re.match(pattern, api.get('text', ''))
        if (regex is not None
                and regex.group('text') == self._keyword_text
                and (regex.group('to') is None
                        or regex.group('to') == self._team.user.id)):
            return True
    return False

def _send_reply(
            self: Ping,
            api: dict) -> None:
    channel = self._team.channel_list.id_search(api.get('channel'))
    if channel is None:
        self._logger.error('unknown channel: {0}'.format(api.get('channel')))
        return
    reply_target = self._team.member_list.id_search(api.get('user'))
    if reply_target is None:
        self._logger.error('unknown target: {0}'.format(api.get('user')))
        return
    reply_text = '<@{0}> {1}'.format(reply_target.id, self._reply_text)
    self._api_call(
                method= 'chat.postMessage',
                text= reply_text,
                channel= channel.id)
