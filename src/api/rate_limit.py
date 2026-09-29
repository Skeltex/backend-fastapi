import math
import time
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from src.core.exceptions.auth_exceptions import TooManyRequestsException

MAX_TRACKED_KEYS = 10_000


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            hits = self._fresh_hits(key, now)
            if len(hits) >= self.limit:
                retry_after = math.ceil(hits[0] + self.window_seconds - now)
                raise TooManyRequestsException(retry_after=max(retry_after, 1))

    def hit(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            if key not in self._hits and len(self._hits) >= MAX_TRACKED_KEYS:
                self._evict(now)
            self._hits.setdefault(key, deque()).append(now)

    @contextmanager
    def guard(self, key: str, *failures: type[Exception]) -> Iterator[None]:
        self.check(key)
        try:
            yield
        except failures:
            self.hit(key)
            raise

    def _fresh_hits(self, key: str, now: float) -> deque[float]:
        hits = self._hits.get(key, deque())
        while hits and hits[0] <= now - self.window_seconds:
            hits.popleft()
        return hits

    def _evict(self, now: float) -> None:
        for key in list(self._hits):
            if not self._fresh_hits(key, now):
                del self._hits[key]
        if len(self._hits) >= MAX_TRACKED_KEYS:
            del self._hits[next(iter(self._hits))]
