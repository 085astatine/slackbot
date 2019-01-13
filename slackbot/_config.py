# -*- coding: utf-8 -*-

import collections
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type
import yaml


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
                 sample: Optional[Any] = None,
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
        self.sample = sample
        self.help = help

    def evaluate(self, data: Dict[str, Any]) -> Any:
        if self.name not in data:
            # required check
            if self.required:
                message = ("the following argument is required '{0:s}'"
                           .format(self.name))
                raise OptionError(message)
        else:
            # choices check
            if self.choices is not None:
                if data[self.name] not in self.choices:
                    message = (
                        "argument '{0}':invalid choice: {1} (choose from {2})"
                        .format(self.name,
                                repr(data[self.name]),
                                ', '.join(map(repr, self.choices))))
                    raise OptionError(message)
        value = data.get(self.name, self.default)
        # type
        if self.type is not None:
            value = self.type(value)
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

    def sample_message(self) -> List[str]:
        result: List[str] = []
        result.append('# {0}'.format(self.help_message()))
        sample = self.sample if self.sample is not None else self.default
        if sample is not None:
            result.extend(
                    yaml.dump({self.name: sample}, default_flow_style=False)
                    .strip()
                    .split('\n'))
        else:
            result.append('{0}:'.format(self.name))
        return result


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
            strline.extend('  {0}'.format(line)
                           for line in option.sample_message())
        return '\n'.join(strline)
