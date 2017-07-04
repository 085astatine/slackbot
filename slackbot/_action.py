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

    def api_call(self, method, **kwargs):
        self._logger.debug("call API '{0}': {1}".format(method, kwargs))
        result = self._client.api_call(method, **kwargs)
        self._logger.log(
                    (_logging.DEBUG
                        if result.get('ok', False)
                        else _logging.ERROR),
                    'result: {0}'.format(result))
        return result

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._config

    @staticmethod
    def option_list():
        return tuple()
