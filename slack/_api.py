# -*- coding: utf-8 -*-

import datetime
from typing import Iterable, Iterator, Tuple, Optional

class Member:
    def __init__(self, data: dict) -> None:
        self.id = data['id'] # type: str
        self.name = data['name'] # type: str
        self.is_bot = data['is_bot'] # type: bool
    
    def __str__(self) -> str:
        str_list = []
        str_list.append(self.name)
        if self.is_bot:
            str_list.append('(Bot)')
        str_list.append('(id: {0.id})'.format(self))
        return ' '.join(str_list)

class MemberList(Iterable[Member]):
    def __init__(
                self,
                member_list: Tuple[Member] = None) -> None:
        self._list = member_list if member_list is not None else ()
        # type: Tuple[Member]
    
    def __iter__(self) -> Iterator[Member]:
        return self._list.__iter__()
    
    def __getitem__(self, key: int) -> Member:
        return self._list.__getitem__(key)
    
    def dump(self) -> str:
        str_list = []
        str_list.append('MemberList')
        str_list.extend(
                    '    {0:03d}: {1}'.format(i, str(member))
                    for i, member in enumerate(self))
        return '\n'.join(str_list)
    
    def id_search(self, member_id: str) -> Optional[Member]:
        for member in self:
            if member.id == member_id:
                return member
        else:
            return None
    
    def name_search(self, name: str) -> Optional[Member]:
        for member in self:
            if member.name == name:
                return member
        else:
            return None

class Channel:
    def __init__(
                self,
                data: dict,
                member_list: MemberList) -> None:
        self.id = data['id']# type: str
        self.name = data['name']# type: str
        self.creator = member_list.id_search(data['creator'])# type: Member
        self.created = datetime.datetime.fromtimestamp(int(data['created']))
        self.members = [
                    member_list.id_search(member_id)
                    for member_id in data['members']]
        self.purpose = data['purpose']['value']
        self.purpose_creator = member_list.id_search(
                    data['purpose']['creator'])
        self.purpose_set = datetime.datetime.fromtimestamp(
                    data['purpose']['last_set'])
        self.topic = data['topic']['value']
        self.topic_creator = member_list.id_search(
                    data['topic']['creator'])
        self.topic_set = datetime.datetime.fromtimestamp(
                    data['topic']['last_set'])
    
    def dump(self) -> str:
        str_list = [] # type: List[str]
        str_list.append('Channel \"{0.name}\" (id: {0.id})'.format(self))
        str_list.append('    creator: {0}'.format(self.creator))
        str_list.append('    created: {0}'.format(self.created))
        str_list.append('    members:')
        str_list.extend('        {0:3d}, {1}'.format(i, member)
                        for i, member in enumerate(self.members))
        str_list.append('    purpose: {0}'.format(self.purpose))
        if self.purpose:
            str_list.append(
                        '        by {0.purpose_creator} at {0.purpose_set}'
                        .format(self))
        str_list.append('    topic: {0}'.format(self.topic))
        if self.topic:
            str_list.append(
                        '        by {0.topic_creator} at {0.topic_set}'
                        .format(self))
        return '\n'.join(str_list)
