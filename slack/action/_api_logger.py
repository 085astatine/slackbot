# -*- coding: utf-8 -*-

import argparse
import logging
import pprint
from typing import List
from .._bot import SlackBotAction, _LogLevelAction

class APILogger(SlackBotAction):
    def __init__(
                self,
                name: str,
                logger: logging.Logger,
                option: argparse.ArgumentParser) -> None:
        SlackBotAction.__init__(self, name, logger)
    
    def action(self, api_list: List[dict]) -> None:
        self._logger.debug('\n{0}'.format(
                    pprint.pformat(api_list, indent= 2)))
    
    @staticmethod
    def option_parser(
                name: str,
                root_parser: argparse.ArgumentParser) \
                -> argparse.ArgumentParser:
        parser = root_parser.add_argument_group(
                    title= '{0} Options'.format(name))
        # Log Level
        parser.add_argument(
                    '--{0}-log-level'.format(name),
                    dest= 'log_level',
                    action= _LogLevelAction,
                    choices= _LogLevelAction.choices(),
                    help= 'set the threshold for the logger')
        return root_parser
