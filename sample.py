#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import slackbot
import slackbot.action


class DummyAction(slackbot.Action):
    @staticmethod
    def option_list():
        return (slackbot.Option('foo', help='bar'),)


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
                             'Download': slackbot.action.Download,
                             'Dummy': DummyAction,
                             'Response': slackbot.action.Response},
                logger=logger)
    bot.initialize()
    bot.start()
