# -*- coding: utf-8 -*-


import logging as _logging


class Action(object):
    def __init__(
                self,
                name,
                config,
                logger=None):
        self._name = name
        self._config = config
        self._client = None
        self._logger = (
                    logger
                    if logger is not None
                    else _logging.getLogger(__name__))

    def setup(self, client):
        self._client = client

    def run(self, api_list):
        pass

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._config

    @staticmethod
    def option_list():
        return tuple()
