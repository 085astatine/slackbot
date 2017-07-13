# -*- coding: utf-8 -*-


import logging as _logging
import re as _re
from .. import Action, Option, unescape_text


class Ping(Action):
    def __init__(
                self,
                name,
                config,
                logger=None):
        Action.__init__(
                    self,
                    name,
                    config,
                    (logger
                        if logger is not None
                        else _logging.getLogger(__name__)))

    def run(self, api_list):
        for api in api_list:
            if api['type'] == 'message' and 'subtype' not in api:
                channel = self.info.channel_list.id_search(api['channel'])
                if channel is None or channel.name not in self.config.channel:
                    continue
                pattern = r'<@(?P<to>[^>]+)>:?\s+(?P<text>.+)'
                regex = _re.match(pattern, api['text'])
                if (regex and
                        regex.group('to') == self.info.bot.id and
                        unescape_text(regex.group('text').strip())
                        == self.config.word):
                    user = self.info.user_list.id_search(api['user'])
                    if user is None:
                        self._logger.error("unknown user id '{0}'"
                                           .format(api['user']))
                        continue
                    reply = '<@{0}> {1}'.format(user.id, self.config.reply)
                    self._logger.info("ping from '{0}' on '{1}'"
                                      .format(user.name, channel.name))
                    self.api_call('chat.postMessage',
                                  text=reply,
                                  channel=channel.id)

    @staticmethod
    def option_list():
        return (
            Option('channel',
                   action=lambda x: [x] if isinstance(x, str) else x,
                   default=[],
                   help='target channel name (list or string)'),
            Option('word',
                   type=str,
                   action=str.strip,
                   default='ping',
                   help='word to react'),
            Option('reply',
                   type=str,
                   default='pong',
                   help='reply message'))