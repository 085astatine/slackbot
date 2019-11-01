# -*- coding: utf-8 -*-

import enum
import re
from typing import Dict, NamedTuple, Optional
from .. import Option, OptionError, OptionList


class IconType(enum.Enum):
    EMOJI = enum.auto()
    URL = enum.auto()

    @staticmethod
    def string_to(value: str) -> Optional['IconType']:
        if re.match(r'^:[^:]+:$', value):
            return IconType.EMOJI
        if re.match(r'https?://[\w/:%#$&\?\(\)~\.\=\+\-]+', value):
            return IconType.URL
        return None


class Icon:
    def __init__(self, value: str) -> None:
        self._value = value
        assert IconType.string_to(self._value) is not None

    @property
    def value(self) -> str:
        return self._value

    @property
    def type(self) -> IconType:
        type_ = IconType.string_to(self.value)
        assert type_ is not None
        return type_

    def __repr__(self) -> str:
        return '{0}.{1}(value={2})'.format(
                self.__class__.__module__,
                self.__class__.__name__,
                repr(self.value))


class AvatarOption(NamedTuple):
    username: Optional[str]
    icon: Optional[Icon]

    def params(self) -> Dict[str, str]:
        result = {}
        if self.username is not None:
            result['username'] = self.username
        if self.icon is not None:
            if self.icon.type is IconType.EMOJI:
                result['icon_emoji'] = self.icon.value
            elif self.icon.type is IconType.URL:
                result['icon_url'] = self.icon.value
        return result

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['AvatarOption']:

        def to_icon(value: Optional[str]) -> Optional[Icon]:
            if value is None:
                return None
            if (isinstance(value, str)
                    and IconType.string_to(value) is not None):
                return Icon(value)
            raise OptionError(
                    'icon is nether an emoji nor a url: {0}'.format(value))

        return OptionList(
            AvatarOption,
            name,
            [Option('username',
                    help='username'),
             Option('icon',
                    action=to_icon,
                    help='user icon (:emoji: or http://url/to/icon)')],
            help=help)
