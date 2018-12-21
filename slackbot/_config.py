# -*- coding: utf-8 -*-

import collections
import sys
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Type


class OptionError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class Option:
    def __init__(self,
                 name: str,
                 action: Optional[Callable[[Any], Any]] = None,
                 default: Optional[Any] = None,
                 type: Optional[Type] = None,
                 choices: Optional[Iterable] = None,
                 required: bool = False,
                 help: str = "") -> None:
        self.name = name
        if action is not None:
            assert callable(action)
        self.action = action
        self.default = default
        if type is not None:
            assert callable(type)
        self.type = type
        if choices is not None:
            assert hasattr(choices, '__iter__')
            assert not isinstance(choices, str)
            assert not isinstance(choices, dict)
        self.choices = choices
        assert isinstance(required, bool)
        self.required = required
        self.help = help

    def evaluate(self, data: Dict[str, Any]) -> Any:
        # required check
        if self.name not in data or data[self.name] is None:
            if self.required:
                message = ("the following argument is required '{0:s}'"
                           .format(self.name))
                raise OptionError(message)
            # return default value
            default = self.default
            if default is not None:
                if isinstance(self.default, str) and self.type is not None:
                    default = self.type(default)
                if self.action is not None:
                    default = self.action(default)
            return default
        value = data[self.name]
        # type
        if callable(self.type):
            value = self.type(value)
        # choices check
        if self.choices is not None:
            if value not in self.choices:
                message = (
                    "argument '{0}':invalid choice: {1} (choose from {2})"
                    .format(self.name,
                            repr(value),
                            ', '.join(map(repr, self.choices))))
                raise OptionError(message)
        # action
        if self.action is not None:
            value = self.action(value)
        return value

    def help_message(self) -> str:
        ss = []
        if len(self.help) != 0:
            ss.append('{0} '.format(self.help))
        if self.choices is not None:
            ss.append('{{{0}}}'.format(', '.join(map(str, self.choices))))
        if isinstance(self.default, (str, int, float, bool)):
            ss.append('(default: {0})'.format(self.default))
        ss.append('({0})'.format('required' if self.required else 'optional'))
        return ''.join(ss)


class ConfigParser:
    def __init__(self, name: str, option_list: Tuple[Option, ...]) -> None:
        self.name = name
        self.option_list = option_list

    def parse(self, data: Optional[Dict[str, Any]]) -> Any:
        if data is None:
            data = {}
        result = {}
        is_error = False
        for option in self.option_list:
            try:
                result[option.name] = option.evaluate(data)
            except OptionError as e:
                sys.stderr.write('{0}\n'.format(str(e)))
                is_error = True
        else:  # check unrecognized arguments
            unused_key_list = sorted(
                        set(data.keys()).difference(
                                option.name for option in self.option_list))
            if len(unused_key_list) != 0:
                is_error = True
                sys.stderr.write(
                        "unrecognized arguments: {0}\n"
                        .format(', '.join(map(repr, unused_key_list))))
        if is_error:
            sys.exit(2)
        """convert: dict -> namedtuple('_', ...), list -> tuple"""
        def convert(value: Any) -> Any:
            if isinstance(value, dict):
                for key in value.keys():
                    value[key] = convert(value[key])
                return collections.namedtuple('_', value.keys())(**value)
            elif isinstance(value, list):
                return tuple(convert(i) for i in value)
            else:
                return value
        # convert each value of result
        for key, value in result.items():
            result[key] = convert(value)
        return collections.namedtuple(
                    "{}Config".format(self.name),
                    result.keys())(**result)

    def help_message(self) -> str:
        strline = []
        strline.append('{0}:'.format(self.name))
        for option in self.option_list:
            strline.append('  # {0}'.format(option.help_message()))
            default = option.default
            if isinstance(default, (str, int, float, bool)):
                strline.append('  {0}: {1}'.format(option.name, default))
            else:
                strline.append('  {0}:'.format(option.name))
        return '\n'.join(strline)
