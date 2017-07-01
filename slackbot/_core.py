# -*- coding: utf-8 -*-


import logging as _logging
from ._action import Action
from ._config import ConfigParser, Option


class Core(Action):
    def __init__(
                self,
                name,
                action_list=None,
                logger=None):
        Action.__init__(
                    self,
                    name,
                    (logger
                        if logger is not None
                        else _logging.getLogger(__name__)))
        self._action_list = (
                    action_list
                    if action_list is not None
                    else dict())

    @staticmethod
    def option_list():
        return tuple()


def create(name, action_list=None, logger=None):
    # logger
    if logger is None:
        logger = _logging.getLogger(__name__)
    # action list
    if action_list is None:
        action_list = dict()
    # config parser
    config_parser_list = []
    config_parser_list.append(ConfigParser('Core', Core.option_list()))
    config_parser_list.extend(
                ConfigParser(key, action_list[key].option_list())
                for key in sorted(action_list.keys()))
    return Core(name,
                action_list={
                    key: action(key)
                    for key, action in action_list.items()},
                logger=logger)
