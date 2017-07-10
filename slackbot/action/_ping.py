# -*- coding: utf-8 -*-


import logging as _logging
from .. import Action, Option


class Ping(Action):
    def __init__(
                self,
                name,
                config,
                logger=None):
        Action.__init__(
                    self,
                    name,
                    config,
                    (logger
                        if logger is not None
                        else _logging.getLogger(__name__)))

    def run(self, api_list):
        pass

    @staticmethod
    def option_list():
        return (
            Option('channel',
                   action=lambda x: [x] if isinstance(x, str) else x,
                   default=[],
                   help='target channel name (list or string)'),
            Option('word',
                   type=str,
                   default='ping',
                   help='word to react'),
            Option('reply',
                   type=str,
                   default='pong',
                   help='reply message'))
