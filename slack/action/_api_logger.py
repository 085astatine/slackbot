# -*- coding: utf-8 -*-

import argparse
import logging
import pprint
from typing import List
from .._bot import SlackBotAction

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
        return root_parser
