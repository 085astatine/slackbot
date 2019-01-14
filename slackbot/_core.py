# -*- coding: utf-8 -*-


import argparse
import collections
import logging
import pathlib
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Type
import yaml
from ._action import Action
from ._client import Client
from ._config import ConfigParser, Option, OptionList
from ._team import Team


class Core(Action):
    def __init__(self,
                 name: str,
                 args: argparse.Namespace,
                 config: Any,
                 action_dict: Dict[str, Action] = None,
                 logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                    name,
                    config,
                    logger=logger or logging.getLogger(__name__))
        self._args = args
        self._action_dict = action_dict or {}
        self._team = Team(
                client=Client(
                    logger=self._logger.getChild('Team')))

    def initialize(self) -> None:
        # load token
        token_file = pathlib.Path(self.config.token_file)
        if not token_file.exists():
            self._logger.error("token file '{0}' does not exist"
                               .format(token_file.resolve().as_posix()))
        with token_file.open() as fin:
            token = fin.read().strip()
        self._logger.info("token file '{0}' has been loaded"
                          .format(token_file.resolve().as_posix()))
        # client, team
        self._client.setup(token)
        self._team.initialize(token)

    def start(self) -> None:
        self._logger.info('connecting to the Real Time Messaging API')
        if self._client.rtm_connect():
            self._logger.info(
                        'connecting to the Real Time Messaging API: success')
            while True:
                timer = threading.Thread(
                            name='CoreTimer',
                            target=lambda: time.sleep(self.config.interval))
                timer.start()
                api_list = self._client.rtm_read()
                for action in self._action_dict.values():
                    action.run(api_list)
                self.run(api_list)
                timer.join()
        else:
            self._logger.error(
                        'connecting to the Real Time Messaging API: failed')

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        self._team.update(api_list)

    @staticmethod
    def option_list(name: str) -> OptionList:
        return OptionList(
            name,
            [Option('token_file',
                    required=True,
                    help='path to the file '
                         'that Slack Authentification token is written'),
             Option('interval',
                    default=1.0,
                    type=float,
                    help='interval(seconds) to read real time messaging API')])


def create(
            name,
            action_dict: Dict[str, Type[Action]] = None,
            logger: Optional[logging.Logger] = None,
            argv: Optional[List[str]] = None) -> Core:
    # check arguments
    if logger is None:
        logger = logging.getLogger(__name__)
    if action_dict is None:
        action_dict = dict()
    if 'Core' in action_dict.keys():
        sys.stderr.write("The keyword 'Core' is reserved\n")
        sys.exit(2)
    assert all(callable(action) for action in action_dict.values())
    # argument parser
    argument_parser = argparse.ArgumentParser(
                description='SlackBot: {0}'.format(name))
    argument_parser.add_argument(
                '--config',
                dest='config',
                type=pathlib.Path,
                metavar='YAML_FILE',
                help='set the configuration file in yaml')
    argument_parser.add_argument(
                '--show-config',
                dest='show_config',
                action='store_true',
                help='output example of configuration file '
                     'to standard output')
    argument_parser.add_argument(
                '-v', '--verbose',
                dest='verbose',
                action='store_true',
                help='set log level to debug')
    option = argument_parser.parse_args(argv)
    # log level
    if option.verbose:
        logger.setLevel(logging.DEBUG)
    logger.debug('command line option: {0}'.format(option))
    # config parser
    config_parser_list: Dict[str, ConfigParser] = collections.OrderedDict()
    config_parser_list['Core'] = ConfigParser(Core.option_list('Core'))
    config_parser_list.update(
                (key, ConfigParser(action_dict[key].option_list(key)))
                for key in sorted(action_dict.keys()))
    # show example of configuration file
    if option.show_config:
        logger.info('output example of configuration file')
        sys.stdout.write('{0}\n'.format(
                    '\n'.join(parser.help_message()
                              for parser in config_parser_list.values())))
        sys.exit(0)
    # load configuration file
    if option.config is None:
        message = 'configuration file is not selected'
        logger.error(message)
        sys.stderr.write('{0}\n'.format(message))
        sys.exit(1)
    elif not option.config.exists():
        message = 'configuration file({0}) does not exit'.format(
                    option.config.as_posix())
        logger.error(message)
        sys.stderr.write('{0}\n'.format(message))
        sys.exit(1)
    config_yaml = yaml.load(option.config.open())
    config_dict = {key: parser.parse(config_yaml.get(key, None))
                   for key, parser in config_parser_list.items()}
    logger.debug('config: {0}'.format(config_dict))
    return Core(name,
                option,
                config_dict['Core'],
                action_dict={
                    key: action(key,
                                config_dict[key],
                                logger=logger.getChild(key))
                    for key, action in action_dict.items()},
                logger=logger)
