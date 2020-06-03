# -*- coding: utf-8 -*-

import enum
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


class Group:
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
    def members(self) -> List[User]:
        return list(filter(
                None,
                map(Team().user_list.id_search,
                    self._data['members'])))

    @property
    def is_archived(self) -> bool:
        return self._data['is_archived']


class UserList:
    def __init__(
            self,
            user_list: Optional[Iterable[User]] = None) -> None:
        self._list = list(user_list) if user_list is not None else []

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
            channel_list: Optional[Iterable[Channel]] = None) -> None:
        self._list = list(channel_list) if channel_list is not None else []

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


class GroupList:
    def __init__(
            self,
            group_list: Optional[Iterable[Group]] = None) -> None:
        self._list = list(group_list) if group_list is not None else []

    def __iter__(self) -> Iterator[Group]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def id_search(self, id: str) -> Optional[Group]:
        return next((group for group in self._list if group.id == id), None)

    def name_search(self, name: str) -> Optional[Group]:
        return next((group for group in self._list if group.name == name),
                    None)

    def add(self, group: Group) -> None:
        self._list.append(group)

    def remove(self, id: str) -> None:
        group = self.id_search(id)
        if group is not None:
            self._list.remove(group)

    def update(self, data: Dict[str, Any]) -> None:
        if 'id' in data:
            group = self.id_search(data['id'])
            if group is not None:
                group.update(data)
            else:
                self.add(Group(data))


class Team:
    class Data:
        auth_test: Dict = {}
        team_info: Dict = {}
        user_list = UserList()
        channel_list = ChannelList()
        group_list = GroupList()

    _data = Data()

    @property
    def url(self) -> str:
        return self._data.auth_test['url']

    @property
    def team_id(self) -> str:
        return self._data.team_info['id']

    @property
    def team_name(self) -> str:
        return self._data.team_info['name']

    @property
    def team_domain(self) -> str:
        return self._data.team_info['domain']

    @property
    def user_list(self) -> UserList:
        return self._data.user_list

    @property
    def channel_list(self) -> ChannelList:
        return self._data.channel_list

    @property
    def group_list(self) -> GroupList:
        return self._data.group_list

    @property
    def bot(self) -> Optional[User]:
        bot_id = self._data.auth_test.get('user_id', None)
        if bot_id is not None:
            return self._data.user_list.id_search(bot_id)
        return None

    async def reset(
            self,
            client: slack.WebClient) -> None:
        # auth.test
        auth_test = await client.auth_test()
        if auth_test.get('ok', False):
            self._data.auth_test = auth_test
        # team.info
        await self.request_team_info(client)
        # users.list
        users_list = await client.users_list()
        if users_list.get('ok', False):
            self._data.user_list = UserList(
                    User(data) for data in users_list['members'])
        # channels.list
        channels_list = await client.channels_list()
        if channels_list.get('ok', False):
            self._data.channel_list = ChannelList(
                    Channel(data) for data in channels_list['channels'])
        # groups.list
        groups_list = await client.groups_list()
        if groups_list.get('ok', False):
            self._data.group_list = GroupList(
                    Group(data) for data in groups_list['groups'])

    async def request_team_info(
            self,
            client: slack.WebClient) -> None:
        # team.info
        team_info = await client.team_info()
        if team_info.get('ok', False):
            self._data.team_info = team_info['team']

    async def request_channels_info(
            self,
            client: slack.WebClient,
            channel_id: str) -> None:
        # channels.info
        response = await client.channels_info(channel=channel_id)
        if response.get('ok', False):
            self._data.channel_list.update(response['channel'])

    async def request_groups_info(
            self,
            client: slack.WebClient,
            group_id: str) -> None:
        # groups.info
        response = await client.groups_info(channel=group_id)
        if response.get('ok', False):
            self._data.group_list.update(response['group'])
