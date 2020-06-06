# -*- cpding: utf-8 -*-

import asyncio
import datetime
import logging
import threading
from typing import Any, List, NamedTuple, Optional, Tuple, TypedDict, Union
import slack
from .. import Action, Option, OptionError, OptionList


class ChannelOption:
    def __init__(self, name: str, period: Union[float, int]) -> None:
        assert isinstance(name, str)
        assert isinstance(period, (float, int))
        self._name = name
        self._period = datetime.timedelta(hours=period)

    def __repr__(self) -> str:
        return "{0}.{1}(name={2}, period={3})".format(
                self.__class__.__module__,
                self.__class__.__name__,
                repr(self._name),
                repr(self._period))

    @property
    def name(self) -> str:
        return self._name

    @property
    def period(self) -> datetime.timedelta:
        return self._period


class ClearHistoryOption(NamedTuple):
    sleep: float
    api_interval: float
    channels: Tuple[ChannelOption, ...]

    @staticmethod
    def option_list(
            name: str,
            help: str = '') -> OptionList['ClearHistoryOption']:
        def parse_channel(data: Any) -> Tuple[ChannelOption, ...]:
            result: List[ChannelOption] = []
            if not (isinstance(data, list)
                    and all(map(lambda x: isinstance(x, dict), data))):
                raise OptionError(
                    'could not convert to ChannelOption\'s list: \'{0}\''
                    .format(data))
            for channel in data:
                try:
                    result.append(ChannelOption(**channel))
                except (AssertionError, TypeError):
                    raise OptionError(
                            'could not convert to ChannelOption: \'{0}\''
                            .format(channel))
            return tuple(result)

        return OptionList(
                ClearHistoryOption,
                name,
                [Option('sleep',
                        type=float,
                        default=float(24 * 60 * 60),
                        help='clear execution interval of (seconds)'),
                 Option('api_interval',
                        type=float,
                        default=5.0,
                        help='slack api execution interval (seconds)'),
                 Option('channels',
                        sample=[{'name': 'CHANNEL_NAME', 'period': 24}],
                        action=parse_channel,
                        help='target channels')],
                help=help)


class _ExecutionStop(Exception):
    pass


class _DeleteTarget(TypedDict):
    channel: str
    ts: str


class ClearHistory(Action[ClearHistoryOption]):
    def __init__(
            self,
            name: str,
            option: ClearHistoryOption,
            logger: Optional[logging.Logger] = None) -> None:
        super().__init__(
                name,
                option,
                logger=logger or logging.getLogger(__name__))
        self._execution_time: Optional[datetime.datetime] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._is_stopped = False

    async def update(self, client: slack.WebClient) -> None:
        if (self.team.is_initialized()
                and not self.is_in_sleep()
                and self._thread is None):
            self._execution_time = _now()
            self._logger.info('execute clear at %s', self._execution_time)
            self._thread = threading.Thread(
                    target=lambda: asyncio.run(self._execute(
                            client=slack.WebClient(
                                    token=client.token,
                                    run_async=True))))
            self._thread.start()
        if self._thread is not None and not self._thread.is_alive():
            self._thread = None

    def stop(self) -> None:
        self._logger.info('request to stop execution')
        with self._lock:
            self._is_stopped = True

    def is_in_sleep(self) -> bool:
        return (self._execution_time is not None
                and (_now() - self._execution_time
                     < datetime.timedelta(seconds=self.option.sleep)))

    async def _execute(self, client: slack.WebClient) -> None:
        try:
            self._logger.info('begin execution')
            # target
            targets: List[_DeleteTarget] = []
            for channel in self.option.channels:
                targets.extend(await self._target_messages(client, channel))
            # delete
            for i, target in enumerate(targets):
                self._logger.debug(
                        'delete %d/%d: channel "%s", %s',
                        i + 1,
                        len(targets),
                        target['channel'],
                        _to_datetime(target['ts']))
                response = await client.chat_delete(**target)
                response.validate()
                await asyncio.sleep(self.option.api_interval)
                self._can_continue()
            self._logger.info('end execution')
        except _ExecutionStop:
            self._logger.info('execution is stopped')
            return

    async def _target_messages(
                self,
                client: slack.WebClient,
                channel_option: ChannelOption) -> List[_DeleteTarget]:
        result: List[_DeleteTarget] = []
        # channel
        channel = self.team.channels.name_search(channel_option.name)
        if channel is None:
            self._logger.warning(
                    'channel \'%s\' is not found',
                    channel_option.name)
            return result
        # latest
        if self._execution_time is None:
            self._logger.error('execution time is None')
            return result
        latest = self._execution_time - channel_option.period
        # request
        for response in await client.conversations_history(
                channel=channel.id,
                latest=str(latest.timestamp()),
                limit=1000):
            response.validate()
            await asyncio.sleep(self.option.api_interval)
            if response['messages']:
                result.extend(
                        {'channel': channel.id,
                         'ts': message['ts']}
                        for message in response['messages'])
                self._logger.debug(
                        'channel "%s": add %d (%s - %s), total %d',
                        channel.name,
                        len(response['messages']),
                        _to_datetime(response['messages'][0]['ts']),
                        _to_datetime(response['messages'][-1]['ts']),
                        len(result))
            self._can_continue()
        if result:
            self._logger.info(
                    'channel "%s": %d target (%s - %s)',
                    channel.name,
                    len(result),
                    _to_datetime(result[0]['ts']),
                    _to_datetime(result[-1]['ts']))
        else:
            self._logger.info('channel "%s": no target', channel.name)
        return result

    def _can_continue(self) -> None:
        with self._lock:
            if self._is_stopped:
                raise _ExecutionStop()

    @staticmethod
    def option_list(name: str) -> OptionList[ClearHistoryOption]:
        return ClearHistoryOption.option_list(name)


def _now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _to_datetime(timestamp: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(float(timestamp))
