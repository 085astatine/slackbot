# -*- coding: utf-8 -*-

import asyncio
import enum
import logging
from typing import Any, Dict, Iterable, Iterator, List, NamedTuple, Optional
import slack


class User:
    def __init__(
            self,
            data: Dict[str, Any]) -> None:
        self._data = data

    def get(self, key: str) -> Any:
        return self._data[key]

    def update(self, data: Dict[str, Any]) -> None:
        self._data.clear()
        self._data.update(data)

    @property
    def id(self) -> str:
        return self._data['id']

    @property
    def name(self) -> str:
        return self._data['name']


class ChannelType(enum.Enum):
    UNKNOWN = enum.auto()
    CHANNEL = enum.auto()
    GROUP = enum.auto()
    IM = enum.auto()
    MPIM = enum.auto()


class ChannelTopic(NamedTuple):
    value: str
    creator: str
    last_set: int


class Channel:
    def __init__(
            self,
            data: Dict[str, Any]) -> None:
        self._data = data

    def get(self, key: str) -> Any:
        return self._data[key]

    def update(self, data: Dict[str, Any]) -> None:
        self._data.clear()
        self._data.update(data)

    @property
    def id(self) -> str:
        return self._data['id']

    @property
    def name(self) -> str:
        return self._data['name']

    @property
    def type(self) -> ChannelType:
        return (
            ChannelType.CHANNEL if self._data.get('is_channel', False)
            else ChannelType.GROUP if self._data.get('is_group', False)
            else ChannelType.IM if self._data.get('is_im', False)
            else ChannelType.MPIM if self._data.get('is_mpim', False)
            else ChannelType.UNKNOWN)

    @property
    def topic(self) -> Optional[ChannelTopic]:
        if 'topic' not in self._data:
            return None
        return ChannelTopic(
                value=self._data['topic']['value'],
                creator=self._data['topic']['creator'],
                last_set=self._data['topic']['last_set'])

    @property
    def purpose(self) -> Optional[ChannelTopic]:
        if 'purpose' not in self._data:
            return None
        return ChannelTopic(
                value=self._data['purpose']['value'],
                creator=self._data['purpose']['creator'],
                last_set=self._data['purpose']['last_set'])

    @property
    def is_archived(self) -> bool:
        return self._data['is_archived']

    @property
    def is_private(self) -> bool:
        return self.type is not ChannelType.CHANNEL


class UserList:
    def __init__(
            self,
            users: Optional[Iterable[User]] = None) -> None:
        self._list = list(users) if users is not None else []

    def __iter__(self) -> Iterator[User]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def id_search(self, id: str) -> Optional[User]:
        return next((user for user in self._list if user.id == id), None)

    def name_search(self, name: str) -> Optional[User]:
        return next((user for user in self._list if user.name == name), None)

    def add(self, user: User) -> None:
        self._list.append(user)

    def remove(self, id: str) -> None:
        user = self.id_search(id)
        if user is not None:
            self._list.remove(user)

    def update(self, data: Dict[str, Any]) -> None:
        if 'id' in data:
            user = self.id_search(data['id'])
            if user is not None:
                user.update(data)
            else:
                self.add(User(data))


class ChannelList:
    def __init__(
            self,
            channels: Optional[Iterable[Channel]] = None) -> None:
        self._list = list(channels) if channels is not None else []

    def __iter__(self) -> Iterator[Channel]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def id_search(self, id: str) -> Optional[Channel]:
        return next((channel for channel in self._list if channel.id == id),
                    None)

    def name_search(self, name: str) -> Optional[Channel]:
        return next(
                (channel for channel in self._list if channel.name == name),
                None)

    def add(self, channel: Channel) -> None:
        self._list.append(channel)

    def remove(self, id: str) -> None:
        channel = self.id_search(id)
        if channel is not None:
            self._list.remove(channel)

    def update(self, data: Dict[str, Any]) -> None:
        if 'id' in data:
            channel = self.id_search(data['id'])
            if channel is not None:
                channel.update(data)
            else:
                self.add(Channel(data))


class Team:
    def __init__(self) -> None:
        self._auth_test: Dict = {}
        self._team_info: Dict = {}
        self._users = UserList()
        self._channels = ChannelList()
        self._is_initialized = False

    @property
    def url(self) -> str:
        return self._auth_test['url']

    @property
    def team_id(self) -> str:
        return self._team_info['id']

    @property
    def team_name(self) -> str:
        return self._team_info['name']

    @property
    def team_domain(self) -> str:
        return self._team_info['domain']

    @property
    def users(self) -> UserList:
        return self._users

    @property
    def channels(self) -> ChannelList:
        return self._channels

    @property
    def bot(self) -> Optional[User]:
        bot_id = self._auth_test.get('user_id', None)
        if bot_id is not None:
            return self._users.id_search(bot_id)
        return None

    async def initialize(
            self,
            client: slack.WebClient,
            *,
            limit: int = 200,
            interval: float = 1.0,
            logger: Optional[logging.Logger] = None) -> None:
        # logging
        if logger:
            logger.debug('begin Team.initialize()')
            if not self._is_initialized:
                logger.warning('Team is already initialized')
        # reset
        await self.reset(
                client,
                limit=limit,
                interval=interval,
                logger=logger)
        self._is_initialized = True
        # logging
        if logger:
            logger.debug('end Team.initialize()')

    def is_initialized(self) -> bool:
        return self._is_initialized

    async def reset(
            self,
            client: slack.WebClient,
            *,
            limit: int = 200,
            interval: float = 1.0,
            logger: Optional[logging.Logger] = None) -> None:
        # logging
        if logger:
            logger.debug('begin Team.reset()')
        # auth.test
        if logger:
            logger.info('request auth.test')
        auth_test = await client.auth_test()
        auth_test.validate()
        self._auth_test = auth_test
        # team.info
        await self.update_team(
                client,
                interval=interval,
                logger=logger)
        # users.list
        await self.update_users(
                client,
                limit=limit,
                interval=interval,
                logger=logger)
        # conversations.list
        await self.update_channels(
                client,
                limit=limit,
                interval=interval,
                logger=logger)
        # logging
        if logger:
            logger.debug('end Team.reset()')

    async def update_team(
            self,
            client: slack.WebClient,
            *,
            interval: float = 1.0,
            logger: Optional[logging.Logger] = None) -> None:
        if logger:
            logger.info('request team.info')
        response = await client.team_info()
        response.validate()
        self._team_info = response['team']
        await asyncio.sleep(interval)

    async def update_users(
            self,
            client: slack.WebClient,
            *,
            limit: int = 200,
            interval: float = 1.0,
            logger: Optional[logging.Logger] = None) -> None:
        if logger:
            logger.info('request conversations.list')
        users: List[Dict] = []
        for response in await client.users_list(limit=limit):
            response.validate()
            users.extend(response['members'])
            if logger:
                logger.debug(
                        'get %d user, total %s',
                        len(response['members']),
                        len(users))
            await asyncio.sleep(interval)
        if logger:
            logger.info('get %d users', len(users))
        self._users = UserList(User(data) for data in users)

    async def update_channels(
            self,
            client: slack.WebClient,
            *,
            limit: int = 200,
            interval: float = 1.0,
            logger: Optional[logging.Logger] = None) -> None:
        if logger:
            logger.info('request conversations.list')
        channels: List[Dict] = []
        for response in await client.conversations_list(limit=limit):
            response.validate()
            channels.extend(response['channels'])
            if logger:
                logger.debug(
                        'get %d channel, total %s',
                        len(response['channels']),
                        len(channels))
            await asyncio.sleep(interval)
        if logger:
            logger.info('get %d channels', len(channels))
        self._channels = ChannelList(Channel(data) for data in channels)

    async def update_channel(
            self,
            client: slack.WebClient,
            channel_id: str,
            *,
            interval: float = 1.0,
            logger: Optional[logging.Logger] = None) -> None:
        if logger:
            logger.info('request conversations.info channel=%s', channel_id)
        response = await client.conversations_info(channel=channel_id)
        if response.get('ok', False):
            self._channels.update(response['channel'])
        elif logger:
            logger.warning('conversations.info failed: %s', response.data)
        await asyncio.sleep(interval)
