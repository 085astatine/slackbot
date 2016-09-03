# -*- coding: utf-8 -*-

import argparse
import logging
from typing import List
from .._bot import SlackBotAction

class Ping(SlackBotAction):
    def __init__(
                self,
                name: str,
                logger: logging.Logger,
                option: argparse.ArgumentParser) -> None:
        SlackBotAction.__init__(self, name, logger)
    
    def action(self, api_list: List[dict]) -> None:
        pass
    
    @staticmethod
    def option_parser(
                name: str,
                root_parser: argparse.ArgumentParser) \
                -> argparse.ArgumentParser:
        parser = root_parser.add_argument_group(
                    title= '{0} Options'.format(name))
        return root_parser
