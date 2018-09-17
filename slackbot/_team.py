# -*- coding: utf-8 -*-

import logging
from typing import Any, Dict, Iterable, Iterator, List, Optional
from ._action import Action
from ._client import Client


_team: Dict[Optional[str], '_Team'] = {}


class User(object):
    def __init__(
            self,
            data: Dict[str, Any],
            key: Optional[str] = None) -> None:
        self._data = data
        self._key = key

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


class Channel(object):
    def __init__(
            self,
            data: Dict[str, Any],
            key: Optional[str] = None) -> None:
        self._data = data
        self._key = key

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
                map(_team[self._key].user_list.id_search,
                    self._data['members'])))

    @property
    def is_archived(self) -> bool:
        return self._data['is_archived']


class Group(object):
    def __init__(
            self,
            data: Dict[str, Any],
            key: Optional[str] = None) -> None:
        self._data = data
        self._key = key

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
                map(_team[self._key].user_list.id_search,
                    self._data['members'])))

    @property
    def is_archived(self) -> bool:
        return self._data['is_archived']


class UserList(object):
    def __init__(
            self,
            user_list: Optional[Iterable[User]] = None,
            key: Optional[str] = None) -> None:
        self._list = list(user_list) if user_list is not None else []
        self._key = key

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


class ChannelList(object):
    def __init__(
            self,
            channel_list: Optional[Iterable[Channel]] = None,
            key: Optional[str] = None) -> None:
        self._list = list(channel_list) if channel_list is not None else []
        self._key = key

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


class GroupList(object):
    def __init__(
            self,
            group_list: Optional[Iterable[Group]] = None,
            key: Optional[str] = None) -> None:
        self._list = list(group_list) if group_list is not None else []
        self._key = key

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


class _Team:
    def __init__(self, key: Optional[str] = None) -> None:
        self._key = key
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
            logger: Optional[logging.Logger] = None) -> None:
        self._key = key
        self._logger = logger or logging.getLogger(__name__)
        if self._key not in _team:
            _team[self._key] = _Team(key=self._key)

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


class TeamUpdate(Action):
    def __init__(self,
                 name: str,
                 config: Any,
                 logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                    name,
                    config,
                    logger or logging.getLogger(__name__))

    def initialize(self, token: str) -> None:
        # client
        self._client.setup(token)
        # auth.test
        auth_test = self.api_call('auth.test')
        bot_id = auth_test['user_id']
        # team info
        team_info = self.api_call('team.info')['team']
        self._logger.debug("team id: '{0}'".format(team_info['id']))
        self._logger.debug("team name: '{0}'".format(team_info['name']))
        # user list
        user_list = UserList(
                    User(user_object)
                    for user_object in self.api_call('users.list')['members'])
        # channel list
        channel_list = ChannelList(
                    Channel(channel_object, user_list)
                    for channel_object
                    in self.api_call('channels.list')['channels'])
        # group list
        group_list = GroupList(
                    Group(group_object, user_list)
                    for group_object in self.api_call('groups.list')['groups'])
        # team
        self._team = Team(
                team_info,
                user_list,
                channel_list,
                group_list,
                bot_id)

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        is_team_updated = False
        updated_channel_id_list = set()
        updated_group_id_list = set()
        for api in api_list:
            api_type = api['type']
            # user_change
            if api_type == 'user_change':
                user = self.team.user_list.id_search(api['user']['id'])
                if user is not None:
                    user.update(api['user'])
            # team join
            elif api_type == 'team_join':
                self.team.user_list.add(User(api['user']))
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
                self.team.channel_list.remove(api['channel'])
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
            self._logger.info('update team')
            self.team._team_info.update(self.api_call('team.info')['team'])
        # update channel
        for channel_id in updated_channel_id_list:
            channel = self.team.channel_list.id_search(channel_id)
            channel_object = self.api_call('channels.info',
                                           channel=channel_id)['channel']
            if channel is not None:
                channel.update(channel_object)
                self._logger.info(
                            "update channel(id:'{0}', name:'{1}')"
                            .format(channel.id, channel.name))
            else:
                self.team.channel_list.add(Channel(
                            channel_object,
                            self.team.user_list))
                channel = self.team.channel_list.id_search(channel_id)
                self._logger.info(
                            "add channel(id:'{0}', name:'{1}')"
                            .format(channel.id, channel.name))
        # update group
        for group_id in updated_group_id_list:
            group = self.team.group_list.id_search(group_id)
            group_object = self.api_call('groups.info',
                                         group=group_id)['group']
            if group is not None:
                group.update(group_object)
                self._logger.info(
                            "update group(id:'{0}', name:'{1}')"
                            .format(group.id, group.name))
            else:
                self.team.group_list.add(Group(
                            group_object,
                            self.team.user_list))
                group = self.team.group_list.id_search(group_id)
                self._logger.info(
                            "add group(id:'{0}', name:'{1}')"
                            .format(group.id, group.name))
