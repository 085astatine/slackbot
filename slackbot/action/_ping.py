# -*- coding: utf-8 -*-


import logging as _logging
from .. import Action


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
