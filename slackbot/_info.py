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
