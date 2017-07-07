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


class UserList(object):
    def __init__(self, user_list):
        self._list = list(user_list)

    def __iter__(self):
        return self._list.__iter__()

    def id_search(self, id):
        return next(filter(lambda user: user.id == id, self._list), None)

    def name_search(self, name):
        return next(filter(lambda user: user.name == name, self._list), None)


class ChannelList(object):
    def __init__(self, channel_list):
        self._list = list(channel_list)

    def __iter__(self):
        return self._list.__iter__()

    def id_search(self, id):
        return next(filter(lambda channel: channel.id == id, self._list), None)

    def name_search(self, name):
        return next(filter(lambda channel: channel.name == name, self._list),
                    None)


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

    def setup(self, client):
        Action.setup(self, client)
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
