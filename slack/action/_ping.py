# -*- coding: utf-8 -*-

import argparse
import logging
from typing import List
from .._bot import SlackBotAction, _LogLevelAction

class Ping(SlackBotAction):
    def __init__(
                self,
                name: str,
                logger: logging.Logger,
                option: argparse.ArgumentParser) -> None:
        SlackBotAction.__init__(self, name, logger)
        # set Log Level
        log_level = getattr(option, '{0}.log_level'.format(self.name))
        if log_level is not None:
            self._logger.setLevel(log_level)
    
    def action(self, api_list: List[dict]) -> None:
        pass
    
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
                    dest= '{0}.log_level'.format(name),
                    action= _LogLevelAction,
                    choices= _LogLevelAction.choices(),
                    help= 'set the threshold for the logger')
        return root_parser
