# -*- coding: utf-8 -*-

import logging
from typing import Any, Dict, Iterable, Iterator, List, Optional
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
    def members(self) -> List[User]:
        return list(filter(
                None,
                map(Team().user_list.id_search,
                    self._data['members'])))

    @property
    def is_archived(self) -> bool:
        return self._data['is_archived']


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
    _auth_test: Dict = {}
    _team_info: Dict = {}
    _user_list = UserList()
    _channel_list = ChannelList()
    _group_list = GroupList()

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
    def user_list(self) -> UserList:
        return self._user_list

    @property
    def channel_list(self) -> ChannelList:
        return self._channel_list

    @property
    def group_list(self) -> GroupList:
        return self._group_list

    @property
    def bot(self) -> Optional[User]:
        bot_id = self._auth_test.get('user_id', None)
        if bot_id is not None:
            return self._user_list.id_search(bot_id)
        return None

    def reset(
            self,
            client: slack.WebClient) -> None:
        # auth.test
        auth_test = client.auth_test()
        if auth_test.get('ok', False):
            self._auth_test = auth_test
        # team.info
        team_info = client.team_info()
        if team_info.get('ok', False):
            self._team_info = team_info['team']
        # users.list
        users_list = client.users_list()
        if users_list.get('ok', False):
            self._user_list = UserList(
                    User(data) for data in users_list['members'])
        # channels.list
        channels_list = client.channels_list()
        if channels_list.get('ok', False):
            self._channel_list = ChannelList(
                    Channel(data) for data in channels_list['channels'])
        # groups.list
        groups_list = client.groups_list()
        if groups_list.get('ok', False):
            self._group_list = GroupList(
                    Group(data) for data in groups_list['groups'])
'''
class _Team:
    def __init__(self, key: Optional[str] = None) -> None:
        self._key = key
        self._ref_count = 1
        self.url: Optional[str] = None
        self.bot_id: Optional[str] = None
        self._team: Dict[str, Any] = {}
        self.user_list = UserList(key=self._key)
        self.channel_list = ChannelList(key=self._key)
        self.group_list = GroupList(key=self._key)

    def reset(self, client: Client) -> None:
        # auth.test
        auth_test = client.api_call('auth.test')
        self.url = auth_test['url']
        self.bot_id = auth_test['user_id']
        # team info
        self._team = client.api_call('team.info')['team']
        # users.list
        self.user_list = UserList(
                    (User(user_data, key=self._key)
                        for user_data
                        in client.api_call('users.list')['members']),
                    key=self._key)
        # channels.list
        self.channel_list = ChannelList(
                    (Channel(channel_data, key=self._key)
                        for channel_data
                        in client.api_call('channels.list')['channels']),
                    key=self._key)
        # groups.list
        self.group_list = GroupList(
                    (Group(group_data, key=self._key)
                        for group_data
                        in client.api_call('groups.list')['groups']),
                    key=self._key)

    def update(
            self,
            client: Client,
            api_list: List[Dict[str, Any]]) -> None:
        is_team_updated = False
        updated_channel_id_list = set()
        updated_group_id_list = set()
        for api in api_list:
            api_type = api['type']
            # user_change
            if api_type == 'user_change':
                self.user_list.update(api['user'])
            # team join
            elif api_type == 'team_join':
                self.user_list.update(api['user'])
            # member_joined_channel, member_left_channel
            elif api_type in ('member_joined_channel', 'member_left_channel'):
                channel_type = api['channel_type']
                if channel_type == 'C':
                    updated_channel_id_list.add(api['channel'])
                elif channel_type == 'G':
                    updated_group_id_list.add(api['channel'])
            # channel_archive, channel_unarchive
            elif api_type in ('channel_archive', 'channel_unarchive'):
                updated_channel_id_list.add(api['channel'])
            # channel_rename
            elif api_type == 'channel_rename':
                updated_channel_id_list.add(api['channel']['id'])
            # channel_created
            elif api_type == 'channel_created':
                updated_channel_id_list.add(api['channel']['id'])
            # channel_deleted
            elif api_type == 'channel_deleted':
                self.channel_list.remove(api['channel'])
            # group_archive, group_unarchive
            elif api_type in ('group_archive', 'group_unarchive'):
                updated_group_id_list.add(api['group'])
            # group_rename
            elif api_type == 'group_rename':
                updated_group_id_list.add(api['group']['id'])
            # team_domain_change, team_rename
            elif api_type in ('team_domain_change', 'team_rename'):
                is_team_updated = True
            # message with subtype
            elif api_type == 'message' and 'subtype' in api:
                subtype = api['subtype']
                # channel_purpose, channel_topic
                if subtype in ('channel_purpose', 'channel_topic'):
                    updated_channel_id_list.add(api['channel'])
                # group_purpose, group_topic
                elif subtype in ('group_purpose', 'group_topic'):
                    updated_group_id_list.add(api['channel'])
        # update team
        if is_team_updated:
            team_info = client.api_call('team.info')
            if team_info.get('ok', False):
                self._team = team_info['team']
        # update channel
        for channel_id in updated_channel_id_list:
            channel_data = client.api_call(
                    'channels.info',
                    channel=channel_id)
            if channel_data.get('ok', False):
                self.channel_list.update(channel_data['channel'])
        # update group
        for group_id in updated_group_id_list:
            group_data = client.api_call(
                    'groups.info',
                    group=group_id)
            if group_data.get('ok', False):
                self.group_list.update(group_data['group'])

    @property
    def team_id(self) -> str:
        return self._team['id']

    @property
    def team_name(self) -> str:
        return self._team['name']

    @property
    def team_domain(self) -> str:
        return self._team['domain']


class Team:
    def __init__(
            self,
            key: Optional[str] = None,
            client: Optional[Client] = None) -> None:
        self._key = key
        self._client = client
        if self._client is not None:
            assert self._key == self._client._key
        # register team
        if self._key not in _team:
            _team[self._key] = _Team(key=self._key)
        else:
            _team[self._key]._ref_count += 1

    def __del__(self):
        _team[self._key]._ref_count -= 1
        if _team[self._key]._ref_count <= 0:
            del _team[self._key]

    def initialize(self, token: str) -> None:
        if self._client is not None:
            self._client.setup(token)
            _team[self._key].reset(self._client)

    def update(self, api_list: List[Dict[str, Any]]) -> None:
        if self._client is not None:
            _team[self._key].update(self._client, api_list)

    @property
    def team_id(self) -> str:
        return _team[self._key].team_id

    @property
    def team_name(self) -> str:
        return _team[self._key].team_name

    @property
    def team_domain(self) -> str:
        return _team[self._key].team_domain

    @property
    def user_list(self) -> UserList:
        return _team[self._key].user_list

    @property
    def channel_list(self) -> ChannelList:
        return _team[self._key].channel_list

    @property
    def group_list(self) -> GroupList:
        return _team[self._key].group_list

    @property
    def bot(self) -> Optional[User]:
        bot_id = _team[self._key].bot_id
        if bot_id is not None:
            return self.user_list.id_search(bot_id)
        else:
            return None
'''
