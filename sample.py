#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from typing import Any, NamedTuple
import slackbot
import slackbot.action


class DummyOption(NamedTuple):
    foo: Any


class DummyAction(slackbot.Action[DummyOption]):
    @staticmethod
    def option_list(name: str) -> slackbot.OptionList:
        return slackbot.OptionList(
            DummyOption,
            name,
            [slackbot.Option('foo', help='bar')])


if __name__ == '__main__':
    logger = logging.getLogger('slackbot')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
                fmt='[%(levelname)s] %(name)s: %(message)s')
    logger.addHandler(handler)
    logger.propagate = False

    bot = slackbot.create(
                'Sample',
                action_dict={'APILogger': slackbot.action.APILogger,
                             'ClearHistory': slackbot.action.ClearHistory,
                             'Download': slackbot.action.Download,
                             'Dummy': DummyAction,
                             'Response': slackbot.action.Response},
                logger=logger)
    bot.start()
