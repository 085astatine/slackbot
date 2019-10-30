# -*- coding: utf-8 -*-

import collections
import time
from typing import Deque, NamedTuple, Optional


class SpeedMeter:
    class Data(NamedTuple):
        value: float
        time: float

    def __init__(self, size: int) -> None:
        self._deque: Deque[SpeedMeter.Data] = collections.deque(maxlen=size)

    def push(self, value: float) -> None:
        self._deque.append(SpeedMeter.Data(
                value=value,
                time=time.perf_counter()))

    def speed(self) -> Optional[float]:
        if self._deque:
            return None
        valuedelta = self._deque[-1].value - self._deque[0].value
        timedelta = self._deque[-1].time - self._deque[0].time
        return valuedelta / timedelta if timedelta != 0 else None


class ProgressReport(NamedTuple):
    file_size: Optional[int]
    downloaded_size: int
    elapsed_time: float
    speed: Optional[float]

    @property
    def remaining_size(self) -> Optional[int]:
        if self.file_size is None:
            return None
        return self.file_size - self.downloaded_size

    @property
    def progress_rate(self) -> Optional[float]:
        if self.file_size is None or self.file_size <= 0:
            return None
        return self.downloaded_size / self.file_size

    @property
    def average_speed(self) -> Optional[float]:
        if self.elapsed_time <= 0:
            return None
        return self.downloaded_size / self.elapsed_time

    @property
    def remaining_time(self) -> Optional[float]:
        if (self.remaining_size is None
                or self.remaining_size < 0
                or self.speed is None
                or self.speed <= 0):
            return None
        return self.remaining_size / self.speed


class Progress:
    def __init__(
            self,
            file_size: Optional[int],
            speedmeter_size: int) -> None:
        self._start_time = time.perf_counter()
        self._latest_time = self._start_time
        self._file_size = file_size
        self._downloaded_size = 0
        self._speedmeter = SpeedMeter(speedmeter_size)
        self._speedmeter.push(0)

    def update(self, received_size: int) -> None:
        self._downloaded_size += received_size
        self._latest_time = time.perf_counter()
        self._speedmeter.push(self._downloaded_size)

    def is_completed(self) -> bool:
        return (self._file_size is None
                or self._file_size == self._downloaded_size)

    def report(self) -> ProgressReport:
        return ProgressReport(
                file_size=self._file_size,
                downloaded_size=self._downloaded_size,
                elapsed_time=self._latest_time - self._start_time,
                speed=self._speedmeter.speed())


class ProgressReportTimer:
    def __init__(self, interval: float) -> None:
        self._last = time.perf_counter()
        self._interval = interval

    def check(self) -> bool:
        current = time.perf_counter()
        if current - self._last >= self._interval:
            self._last = current
            return True
        return False
