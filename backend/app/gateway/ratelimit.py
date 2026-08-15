import threading
import time


class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_per_sec = refill_per_sec
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def try_acquire(self) -> bool:
        with self.lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.refill_per_sec)
            self.updated = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False


class RateLimiter:
    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def set_limit(self, agent_id: str, qps: float) -> None:
        with self._lock:
            self._buckets[agent_id] = TokenBucket(capacity=qps, refill_per_sec=qps)

    def allow(self, agent_id: str) -> bool:
        with self._lock:
            bucket = self._buckets.get(agent_id)
        if bucket is None:
            return True
        return bucket.try_acquire()