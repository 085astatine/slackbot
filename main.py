# -*- coding: utf-8 -*-

import logging
import slack
import slack.action

if __name__ == '__main__':
    # logger
    logger = logging.getLogger('SlackBot')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
                fmt= '%(name)s::%(levelname)s::%(message)s')
    logger.addHandler(handler)
    slack_bot = slack.SlackBot(
                action_list= {
                    'APILogger': slack.action.APILogger,
                    },
                logger= logger)
    slack_bot.run()
