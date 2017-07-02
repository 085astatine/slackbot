# -*- coding: utf-8 -*-


import argparse as _argparse
import collections as _collections
import logging as _logging
import pathlib as _pathlib
import sys as _sys
import yaml as _yaml
from ._action import Action
from ._config import ConfigParser, Option


class Core(Action):
    def __init__(
                self,
                name,
                action_dict=None,
                logger=None):
        Action.__init__(
                    self,
                    name,
                    (logger
                        if logger is not None
                        else _logging.getLogger(__name__)))
        self._action_dict = (
                    action_dict
                    if action_dict is not None
                    else dict())

    @staticmethod
    def option_list():
        return tuple()


def create(
            name,
            action_dict=None,
            logger=None,
            argv=None):
    # logger
    if logger is None:
        logger = _logging.getLogger(__name__)
    # action list
    if action_dict is None:
        action_dict = dict()
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
                action_dict={
                    key: action(key)
                    for key, action in action_dict.items()},
                logger=logger)
