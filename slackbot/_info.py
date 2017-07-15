# -*- coding: utf-8 -*-


import logging
from ._action import Action


class Team(object):
    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._data[key]

    def update(self, data):
        self._data.clear()
        self._data.update(data)

    @property
    def id(self):
        return self._data['id']

    @property
    def name(self):
        return self._data['name']


class User(object):
    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._data[key]

    def update(self, data):
        self._data.clear()
        self._data.update(data)

    @property
    def id(self):
        return self._data['id']

    @property
    def name(self):
        return self._data['name']


class Channel(object):
    def __init__(self, data, user_list):
        self._data = data
        self._user_list = user_list

    def get(self, key):
        return self._data[key]

    def update(self, data):
        self._data.clear()
        self._data.update(data)

    @property
    def id(self):
        return self._data['id']

    @property
    def name(self):
        return self._data['name']

    @property
    def members(self):
        return list(map(self._user_list.id_search, self._data['members']))

    @property
    def is_archived(self):
        return self._data['is_archived']


class Group(object):
    def __init__(self, data, user_list):
        self._data = data
        self._user_list = user_list

    def get(self, key):
        return self._data[key]

    def update(self, data):
        self._data.clear()
        self._data.update(data)

    @property
    def id(self):
        return self._data['id']

    @property
    def name(self):
        return self._data['name']

    @property
    def members(self):
        return list(map(self._user_list.id_search, self._data['members']))

    @property
    def is_archived(self):
        return self._data['is_archived']


class UserList(object):
    def __init__(self, user_list):
        self._list = list(user_list)

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    def id_search(self, id):
        return next((user for user in self._list if user.id == id), None)

    def name_search(self, name):
        return next((user for user in self._list if user.name == name), None)

    def add(self, user):
        self._list.append(user)

    def remove(self, id):
        user = self.id_search(id)
        if user is not None:
            self._list.remove(user)


class ChannelList(object):
    def __init__(self, channel_list):
        self._list = list(channel_list)

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    def id_search(self, id):
        return next((channel for channel in self._list if channel.id == id),
                    None)

    def name_search(self, name):
        return next(
                (channel for channel in self._list if channel.name == name),
                None)

    def add(self, channel):
        self._list.append(channel)

    def remove(self, id):
        channel = self.id_search(id)
        if channel is not None:
            self._list.remove(channel)


class GroupList(object):
    def __init__(self, group_list):
        self._list = list(group_list)

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    def id_search(self, id):
        return next((group for group in self._list if group.id == id), None)

    def name_search(self, name):
        return next((group for group in self._list if group.name == name),
                    None)

    def add(self, group):
        self._list.append(group)

    def remove(self, id):
        group = self.id_search(id)
        if group is not None:
            self._list.remove(group)


class Info(object):
    def __init__(self, team, user_list, channel_list, group_list, bot_id):
        self._team = team
        self._user_list = user_list
        self._channel_list = channel_list
        self._group_list = group_list
        self._bot_id = bot_id

    @property
    def team(self):
        return self._team

    @property
    def user_list(self):
        return self._user_list

    @property
    def channel_list(self):
        return self._channel_list

    @property
    def group_list(self):
        return self._group_list

    @property
    def bot(self):
        return self._user_list.id_search(self._bot_id)


class InfoUpdate(Action):
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
                        else logging.getLogger(__name__)))

    def setup(self, client):
        Action.setup(self, client, None)
        # auth.test
        auth_test = self.api_call('auth.test')
        bot_id = auth_test['user_id']
        # team
        team = Team(self.api_call('team.info')['team'])
        self._logger.debug("team id: '{0}'".format(team.id))
        self._logger.debug("team name: '{0}'".format(team.name))
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
        # info
        self._info = Info(team, user_list, channel_list, group_list, bot_id)

    def run(self, api_list):
        is_team_updated = False
        updated_channel_id_list = set()
        updated_group_id_list = set()
        for api in api_list:
            api_type = api['type']
            # user_change
            if api_type == 'user_change':
                user = self.info.user_list.id_search(api['user']['id'])
                if user is not None:
                    user.update(api['user'])
            # team join
            elif api_type == 'team_join':
                self.info.user_list.add(User(api['user']))
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
                self.info.channel_list.remove(api['channel'])
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
            self.info.team.update(self.api_call('team.info')['team'])
        # update channel
        for channel_id in updated_channel_id_list:
            channel = self.info.channel_list.id_search(channel_id)
            channel_object = self.api_call('channels.info',
                                           channel=channel_id)['channel']
            if channel is not None:
                channel.update(channel_object)
                self._logger.info(
                            "update channel(id:'{0}', name:'{1}')"
                            .format(channel.id, channel.name))
            else:
                self.info.channel_list.add(Channel(
                            channel_object,
                            self.info.user_list))
                channel = self.info.channel_list.id_search(channel_id)
                self._logger.info(
                            "add channel(id:'{0}', name:'{1}')"
                            .format(channel.id, channel.name))
        # update group
        for group_id in updated_group_id_list:
            group = self.info.group_list.id_search(group_id)
            group_object = self.api_call('groups.info',
                                         group=group_id)['group']
            if group is not None:
                group.update(group_object)
                self._logger.info(
                            "update group(id:'{0}', name:'{1}')"
                            .format(group.id, group.name))
            else:
                self.info.group_list.add(Group(
                            group_object,
                            self.info.user_list))
                group = self.info.group_list.id_search(group_id)
                self._logger.info(
                            "add group(id:'{0}', name:'{1}')"
                            .format(group.id, group.name))
