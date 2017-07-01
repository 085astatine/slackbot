# -*- coding: utf-8 -*-


import logging as _logging
from ._action import Action
from ._config import ConfigParser, Option


class Core(Action):
    def __init__(
                self,
                action_list=None,
                logger=None):
        Action.__init__(
                    self,
                    'Core',
                    (logger
                        if logger is not None
                        else _logging.getLogger(__name__)))
        self._action_list = (
                    action_list
                    if action_list is not None
                    else dict())
        # config parser
        config_parser_list = []
        config_parser_list.append(ConfigParser('Core', self.option_list()))
        config_parser_list.extend(
                    ConfigParser(
                                name,
                                self._action_list[name].option_list())
                    for name in sorted(self._action_list.keys()))

    @staticmethod
    def option_list():
        return tuple()
