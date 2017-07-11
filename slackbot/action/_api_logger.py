# -*- coding: utf-8 -*-


import logging as _logging
from .. import Action, Option


class APILogger(Action):
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
        for api in api_list:
            # ignore check
            if (not self.config.output_presence_change and
                    api['type'] == 'presence_change'):
                continue
            if (not self.config.output_user_typing and
                    api['type'] == 'user_typing'):
                continue
            self._logger.info(api)

    @staticmethod
    def option_list():
        return (
            Option('output_presence_change',
                   type=bool,
                   default=True,
                   help='output presence_change'),
            Option('output_user_typing',
                   type=bool,
                   default=True,
                   help='output user_typing'))
