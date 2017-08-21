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
                fmt='%(name)s::%(levelname)s::%(message)s')
    logger.addHandler(handler)

    bot = slackbot.create(
                'Sample',
                action_dict={'APILogger': slackbot.action.APILogger,
                             'Download': slackbot.action.Download,
                             'Dummy': DummyAction,
                             'Ping': slackbot.action.Ping},
                logger=logger)
    bot.setup()
    bot.run()
