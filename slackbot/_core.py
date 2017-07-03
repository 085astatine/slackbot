# -*- coding: utf-8 -*-


import argparse as _argparse
import collections as _collections
import logging as _logging
import pathlib as _pathlib
import sys as _sys
import yaml as _yaml
import slackclient as _slackclient
from ._action import Action
from ._config import ConfigParser, Option


class Core(Action):
    def __init__(
                self,
                name,
                args,
                config,
                action_dict=None,
                logger=None):
        Action.__init__(
                    self,
                    name,
                    config,
                    (logger
                        if logger is not None
                        else _logging.getLogger(__name__)))
        self._args = args
        self._action_dict = (
                    action_dict
                    if action_dict is not None
                    else dict())

    def setup(self):
        # load token
        token_file = self._args.config.parent.joinpath(self.config.token_file)
        if not token_file.exists():
            self._logger.error("token file '{0}' does not exist"
                               .format(token_file.resolve().as_posix()))
        with token_file.open() as fin:
            token = fin.read().strip()
        self._logger.info("token file '{0}' has been loaded"
                          .format(token_file.resolve().as_posix()))
        # client
        Action.setup(self, _slackclient.SlackClient(token))
        for action in self._action_dict.values():
            action.setup(self._client)

    @staticmethod
    def option_list():
        return (
            Option('token_file',
                   required=True,
                   help='path to the file '
                        'that Slack Authentification token is written'),)


def create(
            name,
            action_dict=None,
            logger=None,
            argv=None):
    # check arguments
    if logger is None:
        logger = _logging.getLogger(__name__)
    if action_dict is None:
        action_dict = dict()
    if 'Core' in action_dict.keys():
        _sys.stderr.write("The keyword 'Core' is reserved\n")
        _sys.exit(2)
    assert all(callable(action) for action in action_dict.values())
    # argument parser
    argument_parser = _argparse.ArgumentParser(
                description='SlackBot: {0}'.format(name))
    argument_parser.add_argument(
                '--config',
                dest='config',
                type=_pathlib.Path,
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
        logger.setLevel(_logging.DEBUG)
    logger.debug('command line option: {0}'.format(option))
    # config parser
    config_parser_list = _collections.OrderedDict()
    config_parser_list['Core'] = ConfigParser('Core', Core.option_list())
    config_parser_list.update(
                (key, ConfigParser(key, action_dict[key].option_list()))
                for key in sorted(action_dict.keys()))
    # show example of configuration file
    if option.show_config:
        logger.info('output example of configuration file')
        _sys.stdout.write('{0}\n'.format(
                    '\n'.join(parser.help_message()
                              for parser in config_parser_list.values())))
        _sys.exit(0)
    # load configuration file
    if option.config is None:
        message = 'configuration file is not selected'
        logger.error(message)
        _sys.stderr.write('{0}\n'.format(message))
        _sys.exit(1)
    elif not option.config.exists():
        message = 'configuration file({0}) does not exit'.format(
                    option.config.as_posix())
        logger.error(message)
        _sys.stderr.write('{0}\n'.format(message))
        _sys.exit(1)
    config_yaml = _yaml.load(option.config.open())
    config_dict = {key: parser.parse(config_yaml.get(key, None))
                   for key, parser in config_parser_list.items()}
    logger.debug('config: {0}'.format(config_dict))
    return Core(name,
                option,
                config_dict['Core'],
                action_dict={
                    key: action(key, config_dict[key])
                    for key, action in action_dict.items()},
                logger=logger)
