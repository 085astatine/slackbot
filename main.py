# -*- coding: utf-8 -*-

import logging
import slack

if __name__ == '__main__':
    # logger
    logger = logging.getLogger('SlackBot')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
                fmt= '%(name)s::%(levelname)s::%(message)s')
    logger.addHandler(handler)
    slack_bot = slack.SlackBot(
                logger= logger)
    slack_bot.run()
