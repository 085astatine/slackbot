# -*- coding: utf-8 -*-


class OptionError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Option:
    def __init__(
                self,
                name,
                action=None,
                default=None,
                type=None,
                choices=None,
                required=False,
                help=""):
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

    def evaluate(self, data):
        # required check
        if self.name not in data:
            if self.required:
                message = ("the following argument is required '{0:s}'"
                           .format(self.name))
                raise OptionError(message)
            return self.default  # return default value
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
                            ', '.join(repr(c) for c in self.choices)))
                raise OptionError(message)
        # action
        if self.action is not None:
            value = self.action(value)
        return value
