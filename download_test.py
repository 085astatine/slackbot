#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import pathlib
import time
from typing import List
import slackbot.action


if __name__ == '__main__':
    # logger
    logger = logging.getLogger('download')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
                fmt='%(name)s::%(levelname)s::%(message)s')
    logger.addHandler(handler)
    # load url list
    url_list = []
    with pathlib.Path('url_list.txt').open() as fin:
        url_list = [url for url in fin.read().split('\n') if len(url) != 0]
    print(url_list)
    # create download observer
    observer_list: List[str] = []
    for i, url in enumerate(url_list):
        observer_list.append(slackbot.action.DownloadObserver(
                    'result{0:02d}'.format(i),
                    url,
                    logger=logger))
    # start download
    for observer in observer_list:
        observer.start()
    # wait
    while not all(map(lambda observer: observer.is_finished(), observer_list)):
        time.sleep(1)
