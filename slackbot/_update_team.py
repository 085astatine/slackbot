# -*- coding: utf-8 -*-

import logging
import time
from typing import Callable, Dict, NamedTuple, Optional
import slack
from ._action import Action
from ._option import Option, OptionList


class UpdateTeamOption(NamedTuple):
    reset_interval: float

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['UpdateTeamOption']:
        return OptionList(
            UpdateTeamOption,
            name,
            [Option('reset_interval',
                    action=lambda x: float(x) if x is not None else None,
                    default=None,
                    help='interval seconds to reset team info')],
            help=help)


class UpdateTeam(Action[UpdateTeamOption]):
    def __init__(
            self,
            name: str,
            option: UpdateTeamOption,
            logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                name,
                option,
                logger=logger or logging.getLogger(__name__))
        self._last_reset_time = time.perf_counter()

    def register(self) -> None:
        # open
        self.register_callback(
                event='open',
                callback=self._initialize)
        # team_domain_change, team_rename
        for event in ('team_domain_change', 'team_rename'):
            self.register_callback(
                    event=event,
                    callback=self._update_team)
        # user_change, team_join
        for event in ('user_change', 'team_join'):
            self.register_callback(
                    event=event,
                    callback=self._update_user(lambda x: x['user']))
        # channel_rename, channel_created, group_rename
        for event in ('channel_rename', 'channel_created', 'group_rename'):
            self.register_callback(
                    event=event,
                    callback=self._update_channel(
                            lambda x: x['channel']['id']))
        # channel_archive, channel_unarchive, group_archive, group_unarchive
        for event in (
                'channel_archive', 'channel_unarchive',
                'group_archive', 'group_unarchive'):
            self.register_callback(
                    event=event,
                    callback=self._update_channel(lambda x: x['channel']))
        # channel_delete, group_deleted
        for event in ('channel_deleted', 'group_deleted'):
            self.register_callback(
                    event=event,
                    callback=self._delete_channel(lambda x: x['channel']))
        # message
        self.register_callback(
                event='message',
                callback=self._message)

    async def update(self, client: slack.WebClient) -> None:
        if self.option.reset_interval is None:
            return
        current = time.perf_counter()
        if (current - self._last_reset_time) > self.option.reset_interval:
            self._logger.debug(
                    'reset team (interval %f s)',
                    current - self._last_reset_time)
            self._last_reset_time = current
            await self.team.reset(client)

    async def _initialize(self, **payload) -> None:
        self._logger.debug('initialze team')
        client: Optional[slack.WebClient] = payload.get('web_client', None)
        if client is not None:
            await self.team.reset(client)

    async def _update_team(self, **payload) -> None:
        client: Optional[slack.WebClient] = payload.get('web_client', None)
        if client is not None:
            await self.team.request_team_info(client)

    def _update_user(self, get_user: Callable[[Dict], Dict]) -> Callable:
        def callback(**payload) -> None:
            data = payload['data']
            self.team.users.update(get_user(data))
        return callback

    def _update_channel(self, get_id: Callable[[Dict], str]) -> Callable:
        def callback(**payload) -> None:
            data = payload['data']
            client: Optional[slack.WebClient] = payload.get('web_client', None)
            if client is not None:
                self.team.request_conversations_info(client, get_id(data))
        return callback

    def _delete_channel(self, get_id: Callable[[Dict], str]) -> Callable:
        def callback(**payload) -> None:
            data = payload['data']
            self.team.channels.remove(get_id(data))
        return callback

    async def _message(self, **payload) -> None:
        data = payload['data']
        client: Optional[slack.WebClient] = payload.get('web_client', None)
        subtype = data.get('subtype', None)
        if subtype in (
                'channel_purpose', 'channel_topic',
                'group_purpose', 'group_topic'):
            await self.team.request_conversations_info(client, data['channel'])
