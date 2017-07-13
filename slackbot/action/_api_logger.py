# -*- coding: utf-8 -*-


import enum as _enum
import logging as _logging
import pprint as _pprint
from .. import Action, Option


class Mode(_enum.Enum):
    raw = _enum.auto()
    pprint = _enum.auto()


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
            # raw
            if self.config.mode is Mode.raw:
                self._logger.info(api)
            # pprint
            elif self.config.mode is Mode.pprint:
                self._logger.info(
                        '\n{0}'.format(_pprint.pformat(api, indent=2)))

    @staticmethod
    def option_list():
        return (
            Option('mode',
                   action= lambda mode: getattr(Mode, mode),
                   default='raw',
                   choices=[mode.name for mode in Mode],
                   help='output format'),
            Option('output_presence_change',
                   type=bool,
                   default=True,
                   help='output presence_change'),
            Option('output_user_typing',
                   type=bool,
                   default=True,
                   help='output user_typing'))
