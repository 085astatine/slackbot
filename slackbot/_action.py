# -*- coding: utf-8 -*-


import logging as _logging


class Action(object):
    def __init__(
                self,
                name,
                config,
                logger=None):
        self.name = name
        self.config = config
        self._client = None
        self._logger = (
                    logger
                    if logger is not None
                    else _logging.getLogger(__name__))

    def setup(self, client):
        self._client = client

    @staticmethod
    def option_list():
        return tuple()
