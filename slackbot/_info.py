# -*- coding: utf-8 -*-


import logging as _logging
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
        return next(filter(lambda user: user.id == id, self._list), None)

    def name_search(self, name):
        return next(filter(lambda user: user.name == name, self._list), None)


class ChannelList(object):
    def __init__(self, channel_list):
        self._list = list(channel_list)

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    def id_search(self, id):
        return next(filter(lambda channel: channel.id == id, self._list), None)

    def name_search(self, name):
        return next(filter(lambda channel: channel.name == name, self._list),
                    None)


class Info(object):
    def __init__(self, team, user_list, channel_list, bot_id):
        self._team = team
        self._user_list = user_list
        self._channel_list = channel_list
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
                        else _logging.getLogger(__name__)))
        self._info = None

    def setup(self, client):
        Action.setup(self, client)
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
        group_list = list(
                    Group(group_object, user_list)
                    for group_object in self.api_call('groups.list')['groups'])
        # info
        self._info = Info(team, user_list, channel_list, bot_id)

    @property
    def info(self):
        return self._info
