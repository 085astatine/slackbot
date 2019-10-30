# -*- coding: utf-8 -*-

import enum
import logging
import random
import re
from collections import OrderedDict
from typing import (
        Any, Dict, Iterable, List, NamedTuple, Optional, Tuple, Union)
import slack
from .. import Action, Option, OptionError, OptionList, unescape_text


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
        assert all(map(lambda x: isinstance(x, str), self.call))
        # response
        self.response: Tuple[str, ...]
        if isinstance(response, str):
            self.response = (response,)
        else:
            self.response = tuple(response)
        assert all(map(lambda x: isinstance(x, str), self.response))

    def __repr__(self) -> str:
        return "{0}.{1}(call={2}, response={3})".format(
                self.__class__.__module__,
                self.__class__.__name__,
                repr(self.call),
                repr(self.response))


class ResponseOption(NamedTuple):
    channel: List[str]
    trigger: Trigger
    pattern: Tuple[Pattern, ...]
    username: Optional[str]
    icon: Optional[str]

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['ResponseOption']:
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
            elif data is not None:
                message = (
                    'could not convert to Pattern\'s list: \'{0}\''
                    .format(data))
                raise OptionError(message)
            return result

        return OptionList(
            ResponseOption,
            name,
            [Option('channel',
                    action=lambda x: (
                            [] if x is None
                            else [x] if isinstance(x, str)
                            else x),
                    default=None,
                    help='target channel name (list or string)'),
             Option('trigger',
                    default='non-reply',
                    action=lambda x: to_trigger.get(x),
                    choices=to_trigger.keys(),
                    help='response trigger'),
             Option('pattern',
                    sample=[{'call': ['ping'], 'response': ['pong']}],
                    action=parse_pattern_list,
                    help='response pattern'),
             Option('username',
                    help='username'),
             Option('icon',
                    action=_check_icon,
                    help='user icon (:emoji: or http://url/to/icon)')],
            help=help)


class Response(Action[ResponseOption]):
    def __init__(
            self,
            name: str,
            option: ResponseOption,
            logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                name,
                option,
                logger=logger or logging.getLogger(__name__))

    def register(self) -> None:
        self.register_callback(
                event='message',
                callback=self._response)

    @staticmethod
    def option_list(name: str) -> OptionList[ResponseOption]:
        return ResponseOption.option_list(name)

    def _response(self, **payload) -> None:
        data = payload['data']
        client: Optional[slack.WebClient] = payload['web_client']
        channel = self.team.channel_list.id_search(data['channel'])
        if ('subtype' in data
                or channel is None
                or channel.name not in self.option.channel
                or client is None):
            return
        # user
        user = self.team.user_list.id_search(data['user'])
        if user is None:
            return
        # message text
        match = re.search(
                    r'(<@(?P<reply_to>[^|>]+)(|\|.+)>|)\s*(?P<text>.+)',
                    data['text'])
        if not match:
            return
        text = unescape_text(match.group('text'))
        # trigger
        is_reply = (self.team.bot is not None
                    and match.group('reply_to') == self.team.bot.id)
        if ((is_reply and self.option.trigger is Trigger.NON_REPLY)
                or (not is_reply and self.option.trigger is Trigger.REPLY)):
            return
        # pattern
        for pattern in self.option.pattern:
            if text not in pattern.call:
                continue
            params = {}
            # text
            response = random.choice(pattern.response)
            params['text'] = '{0}{1}'.format(
                    '<@{0}> '.format(user.id) if is_reply else '',
                    response)
            # username
            if self.option.username is not None:
                params['username'] = self.option.username
            # icon
            if self.option.icon is not None:
                if _is_emoji(self.option.icon):
                    params['icon_emoji'] = self.option.icon
                elif _is_url(self.option.icon):
                    params['icon_url'] = self.option.icon
            # request
            self._logger.info(
                    'response: \'%s\' (from \'%s\') -> \'%s\'',
                    text,
                    user.name,
                    response)
            self._logger.debug('params: %r', params)
            client.chat_postMessage(
                    channel=channel.id,
                    **params)


def _is_url(value: str) -> bool:
    return bool(re.match(r'https?://[\w/:%#$&\?\(\)~\.\=\+\-]+', value))


def _is_emoji(value: str) -> bool:
    return bool(re.match(':[^:]+:', value))


def _check_icon(value: Optional[str]) -> Optional[str]:
    if value is not None and not (_is_emoji(value) or _is_url(value)):
        message = (
                'icon is nether an emoji nor a url: {0}'
                .format(value))
        raise OptionError(message)
    return value
