# -*- coding: utf-8 -*-

import copy
import enum
import logging
import random
import re
from typing import Dict, Iterable, List, NamedTuple, Optional, Tuple
import slack
from .. import Action, Option, OptionError, OptionList, unescape_text
from ._option import AvatarOption


class Trigger(enum.Enum):
    NON_REPLY = enum.auto()
    REPLY = enum.auto()
    ANY = enum.auto()


class Pattern:
    def __init__(
            self,
            call: Iterable[str],
            response: Iterable[str]) -> None:
        self._call: Tuple[str, ...] = tuple(call)
        self._response: Tuple[str, ...] = tuple(response)
        assert all(map(lambda x: isinstance(x, str), self.call))
        assert all(map(lambda x: isinstance(x, str), self.response))

    def __repr__(self) -> str:
        return "{0}.{1}(call={2}, response={3})".format(
                self.__class__.__module__,
                self.__class__.__name__,
                repr(self.call),
                repr(self.response))

    @property
    def call(self) -> Tuple[str, ...]:
        return self._call

    @property
    def response(self) -> Tuple[str, ...]:
        return self._response


class ResponseOption(NamedTuple):
    channel: Tuple[str, ...]
    trigger: Trigger
    pattern: Tuple[Pattern, ...]
    avatar: AvatarOption

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['ResponseOption']:
        # translate to Trigger
        to_trigger: Dict[str, Trigger] = {
                'non-reply': Trigger.NON_REPLY,
                'reply': Trigger.REPLY,
                'any': Trigger.ANY}

        # translate to Pattern
        def parse_pattern(data) -> Pattern:
            kwargs = copy.deepcopy(data)
            if isinstance(kwargs, dict):
                for key in ('call', 'response'):
                    if key in kwargs and isinstance(kwargs[key], str):
                        kwargs[key] = [kwargs[key]]
            try:
                return Pattern(**kwargs)
            except (TypeError, AssertionError):
                raise OptionError(
                        'could not convert to Pattern: \'{0}\''.format(data))

        # translate to list of Patterns
        def parse_pattern_list(data) -> List[Pattern]:
            if isinstance(data, dict):
                return [parse_pattern(data)]
            if isinstance(data, Iterable) and not isinstance(data, str):
                return [parse_pattern(element) for element in data]
            if data is None:
                return []
            raise OptionError(
                    'could not convert to Pattern\'s list: \'{0}\''
                    .format(data))

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
                    action=to_trigger.get,
                    choices=to_trigger.keys(),
                    help='response trigger'),
             Option('pattern',
                    sample=[{'call': ['ping'], 'response': ['pong']}],
                    action=parse_pattern_list,
                    help='response pattern'),
             AvatarOption.option_list(
                    name='avatar',
                    help='avatar')],
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
            # avatar
            params.update(self.option.avatar.params())
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
