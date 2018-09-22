# -*- coding: utf-8 -*-

import enum
import logging
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple
from .. import Action, Option, unescape_text
from .._team import Channel, User


class Trigger(enum.Enum):
    NON_REPLY = enum.auto()
    REPLY = enum.auto()
    ANY = enum.auto()


class Response(Action):
    def __init__(
            self,
            name: str,
            config: Any,
            key: Optional[str] = None,
            logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                name,
                config,
                key=key,
                logger=logger or logging.getLogger(__name__))

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        for api in api_list:
            if api['type'] == 'message' and 'subtype' not in api:
                channel = self.team.channel_list.id_search(api['channel'])
                if channel is None or channel.name not in self.config.channel:
                    continue
                user = self.team.user_list.id_search(api['user'])
                if user is None:
                    continue
                _response(
                        self,
                        user,
                        channel,
                        api['text'])

    @staticmethod
    def option_list() -> Tuple[Option, ...]:
        # translate: str -> Trigger
        to_trigger: Dict[str, Trigger] = OrderedDict()
        to_trigger['non-reply'] = Trigger.NON_REPLY
        to_trigger['reply'] = Trigger.REPLY
        to_trigger['any'] = Trigger.ANY
        return (
            Option('channel',
                   action=lambda x: [x] if isinstance(x, str) else x,
                   default=[],
                   help='target channel name (list or string)'),
            Option('trigger',
                   default='non-reply',
                   action=lambda x: to_trigger.get(x),
                   choices=to_trigger.keys(),
                   help='response trigger'),
            Option('word',
                   type=str,
                   action=str.strip,
                   default='ping',
                   help='word to react'),
            Option('reply',
                   type=str,
                   default='pong',
                   help='reply message'))


def _response(
        self: Response,
        user: User,
        channel: Channel,
        message: str) -> None:
    match = re.search(
            r'(<@(?P<reply_to>[^|>]+)(|\|.+)>|)\s*(?P<text>.+)',
            message)
    if not match:
        return
    if unescape_text(match.group('text')).strip() != self.config.word:
        return
    # create response
    response = ""
    if (self.team.bot is not None
            and match.group('reply_to') == self.team.bot.id):
        response += "<@{0}> ".format(user.id)
        if self.config.trigger == Trigger.NON_REPLY:
            return
    elif self.config.trigger == Trigger.REPLY:
        return
    response += self.config.reply
    # api call
    self._logger.info(
            "call from '{0}' on '{1}'".format(user.name, channel.name))
    self.api_call(
            'chat.postMessage',
            text=response,
            channel=channel.id)
