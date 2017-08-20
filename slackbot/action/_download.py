# -*- coding: utf-8


import logging
from typing import Any, Dict, List, Optional, Tuple
from .. import Action, Option


class Download(Action):
    def __init__(self,
                 name: str,
                 config: Any,
                 logger: Optional[logging.Logger] = None) -> None:
        Action.__init__(
                    self,
                    name,
                    config,
                    (logger
                        if logger is not None
                        else logging.getLogger(__name__)))

    def run(self, api_list: List[Dict[str, Any]]) -> None:
        pass

    @staticmethod
    def option_list() -> Tuple[Option, ...]:
        return tuple()
