# -*- coding: utf-8 -*-

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
