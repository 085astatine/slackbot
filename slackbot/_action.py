# -*- coding: utf-8 -*-


import logging as _logging


class Action(object):
    def __init__(
                self,
                name,
                logger=None):
        self.name = name
        self._logger = (
                    logger
                    if logger is not None
                    else _logging.getLogger(__name__))

    @staticmethod
    def option_list():
        return tuple()
