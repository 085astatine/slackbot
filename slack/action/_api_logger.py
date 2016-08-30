# -*- coding: utf-8 -*-

import argparse
import logging
import pprint
from typing import List
from .._bot import SlackBotAction, _LogLevelAction

class APILogger(SlackBotAction):
    def __init__(
                self,
                logger: logging.Logger,
                option: argparse.ArgumentParser) -> None:
        SlackBotAction.__init__(self, logger)
    
    def action(self, api_list: List[dict]) -> None:
        self._logger.debug('\n{0}'.format(
                    pprint.pformat(api_list, indent= 2)))
    
    @staticmethod
    def option_parser(
                root_parser: argparse.ArgumentParser) \
                -> argparse.ArgumentParser:
        parser = root_parser.add_argument_group(
                    title= 'APILogger Options')
        # Log Level
        parser.add_argument(
                    '--APILogger-log-level',
                    dest= 'log_level',
                    action= _LogLevelAction,
                    choices= ('debug', 'info', 'warning', 'error', 'critical'),
                    help= 'set the threshold for the logger')
        return root_parser