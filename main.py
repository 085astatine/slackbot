# -*- coding: utf-8 -*-

import pathlib
from typing import Optional
import slack

def load_token() -> Optional[str]:
    token_file = pathlib.Path('SLACK_TOKEN')
    if token_file.exists():
        with token_file.open() as file:
            token = file.read().strip()
        return token
    else:
        return None

if __name__ == '__main__':
    token = load_token()
    if token is not None:
        slack_bot = slack.SlackBot(token)
        slack_bot.run()
