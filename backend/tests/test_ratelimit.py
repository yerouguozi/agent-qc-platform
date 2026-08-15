import time

from app.gateway.ratelimit import RateLimiter


def test_block_after_burst():
    limiter = RateLimiter()
    limiter.set_limit("a", qps=2)
    assert limiter.allow("a")
    assert limiter.allow("a")
    assert not limiter.allow("a")


def test_refill_after_wait():
    limiter = RateLimiter()
    limiter.set_limit("a", qps=4)
    limiter.allow("a")
    time.sleep(0.3)
    assert limiter.allow("a")


def test_unregistered_allowed():
    limiter = RateLimiter()
    assert limiter.allow("ghost")