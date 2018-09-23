# -*- coding: utf-8 -*-

import enum
import logging
import random
import re
from collections import OrderedDict
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from .. import Action, Option, OptionError, unescape_text
from .._team import Channel, User


class Trigger(enum.Enum):
    NON_REPLY = enum.auto()
    REPLY = enum.auto()
    ANY = enum.auto()


class Pattern:
    def __init__(
            self,
            call: Union[str, Iterable[str]],
            response: Union[str, Iterable[str]]) -> None:
        # call
        self.call: Tuple[str, ...]
        if isinstance(call, str):
            self.call = (call,)
        else:
            self.call = tuple(call)
        assert(all(map(lambda x: isinstance(x, str), self.call)))
        # response
        self.response: Tuple[str, ...]
        if isinstance(response, str):
            self.response = (response,)
        else:
            self.response = tuple(response)
        assert(all(map(lambda x: isinstance(x, str), self.response)))

    def __repr__(self) -> str:
        return "{0}.{1}(call={2}, response={3})".format(
                self.__class__.__module__,
                self.__class__.__name__,
                repr(self.call),
                repr(self.response))


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
        # translate to Trigger
        to_trigger: Dict[str, Trigger] = OrderedDict()
        to_trigger['non-reply'] = Trigger.NON_REPLY
        to_trigger['reply'] = Trigger.REPLY
        to_trigger['any'] = Trigger.ANY

        # translate to Pattern
        def parse_pattern(data: Any) -> Pattern:
            if isinstance(data, Pattern):
                return data
            # type check
            elif (isinstance(data, dict)
                    and 'call' in data
                    and (isinstance(data['call'], str)
                         or (hasattr(data['call'], '__iter__')
                             and all(map(lambda x: isinstance(x, str),
                                         data['call']))))
                    and 'response' in data
                    and (isinstance(data['response'], str)
                         or (hasattr(data['response'], '__iter__')
                             and all(map(lambda x: isinstance(x, str),
                                         data['response']))))
                    and len(data) == 2):
                return Pattern(**data)
            else:
                message = (
                        'could not convert to Pattern: \'{0}\''
                        .format(data))
                raise OptionError(message)

        # translate to list of Patterns
        def parse_pattern_list(data: Any) -> List[Pattern]:
            result: List[Pattern] = []
            if isinstance(data, dict):
                result.append(parse_pattern(data))
            elif hasattr(data, '__iter__') and not isinstance(data, str):
                for element in data:
                    result.append(parse_pattern(element))
            else:
                message = (
                    'could not convert to Pattern\'s list: \'{0}\''
                    .format(data))
                raise OptionError(message)
            return result

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
            Option('pattern',
                   default=(Pattern(call='ping', response='pong'),),
                   action=parse_pattern_list,
                   help='response pattern'
                        ' (default: [{call: ping, response: pong}])'))


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
    text = unescape_text(match.group('text'))
    for pattern in self.config.pattern:
        if text not in pattern.call:
            continue
        # create response
        response = ""
        if (self.team.bot is not None
                and match.group('reply_to') == self.team.bot.id):
            response += "<@{0}> ".format(user.id)
            if self.config.trigger == Trigger.NON_REPLY:
                return
        elif self.config.trigger == Trigger.REPLY:
            return
        response += random.choice(pattern.response)
        # api call
        self._logger.info(
                "call from '{0}' on '{1}'".format(user.name, channel.name))
        self.api_call(
                'chat.postMessage',
                text=response,
                channel=channel.id)
