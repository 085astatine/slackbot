# -*- coding: utf-8 -*-

import collections
import sys
from typing import (
        Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple,
        Type, Union)
import yaml


class OptionError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class InputValue(NamedTuple):
    is_none: bool = True
    value: Any = None


class Option:
    def __init__(self,
                 name: str,
                 action: Optional[Callable[[Any], Any]] = None,
                 default: Optional[Any] = None,
                 type: Optional[Type] = None,
                 choices: Optional[Iterable] = None,
                 required: bool = False,
                 sample: Optional[Any] = None,
                 help: str = '') -> None:
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

    def evaluate(self, input_: InputValue) -> Any:
        if input_.is_none:
            # required check
            if self.required:
                message = ("the following argument is required '{0:s}'"
                           .format(self.name))
                raise OptionError(message)
        else:
            # choices check
            if self.choices is not None:
                if input_.value not in self.choices:
                    message = (
                        "argument '{0}':invalid choice: {1} (choose from {2})"
                        .format(self.name,
                                repr(input_.value),
                                ', '.join(map(repr, self.choices))))
                    raise OptionError(message)
        value = input_.value if not input_.is_none else self.default
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

    def sample_message(self, indent: int = 0) -> List[str]:
        line: List[str] = []
        line.append('{0}# {1}'.format(' ' * indent, self.help_message()))
        sample = self.sample if self.sample is not None else self.default
        if sample is not None:
            yaml_text = yaml.dump(
                    {self.name: sample},
                    default_flow_style=False)
            line.extend('{0}{1}'.format(' ' * indent, line)
                        for line in yaml_text.strip().split('\n'))
        else:
            line.append('{0}{1}:'.format(' ' * indent, self.name))
        return line


class OptionList:
    def __init__(
            self,
            name: str,
            options: Iterable[Union[Option, 'OptionList']],
            help: str = '') -> None:
        self.name = name
        self._list: List[Union[Option, 'OptionList']] = list(options)
        self.help = help

    def evaluate(self, input_: InputValue):
        if input_.is_none:
            input_ = InputValue(is_none=True, value={})
        result = {}
        is_error = False
        for option in self._list:
            child_input = InputValue(
                    is_none=option.name not in input_.value,
                    value=input_.value.get(option.name, None))
            try:
                result[option.name] = option.evaluate(child_input)
            except OptionError as e:
                sys.stderr.write('{0}\n'.format(str(e)))
                is_error = True
        # check unrecognized arguments
        unused_key_list = sorted(
                    set(input_.value.keys())
                    .difference(option.name for option in self._list))
        if len(unused_key_list) != 0:
            is_error = True
            sys.stderr.write(
                    '{0} has unrecognized arguments: {1}\n'
                    .format(self.name, ', '.join(map(repr, unused_key_list))))
        if is_error:
            sys.exit(2)
        """to immutable: dict -> namedtuple('_', ...), list -> tuple"""
        def to_immutable(value: Any) -> Any:
            if isinstance(value, dict):
                for key in value.keys():
                    value[key] = to_immutable(value[key])
                return collections.namedtuple('_', value.keys())(**value)
            elif isinstance(value, list):
                return tuple(to_immutable(i) for i in value)
            else:
                return value
        return collections.namedtuple(
                '{0}Option'.format(self.name),
                result.keys())(
                        **dict((key, to_immutable(value))
                               for key, value in result.items()))

    def sample_message(self, indent: int = 0) -> List[str]:
        line = []
        if self.help:
            line.append('{0}# {1}'.format(' ' * indent, self.help))
        line.append('{0}{1}:'.format(' ' * indent, self.name))
        for option in self._list:
            line.extend(option.sample_message(indent + 2))
        return line


class ConfigParser:
    def __init__(self, name: str, option_list: Tuple[Option, ...]) -> None:
        self._option_list = OptionList(name, option_list)

    def parse(self, data: Optional[Dict[str, Any]]) -> Any:
        input_ = InputValue(False, data if data is not None else {})
        return self._option_list.evaluate(input_)

    def help_message(self) -> str:
        return '\n'.join(self._option_list.sample_message(indent=0))
