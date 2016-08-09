# -*- coding: utf-8 -*-

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
