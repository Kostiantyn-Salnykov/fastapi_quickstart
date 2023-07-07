import abc
import datetime
import functools
import typing

import pendulum
from fastapi import Depends, Request, Response

import redis.asyncio as aioredis
from apps.CORE.deps import get_redis
from apps.CORE.enums import RatePeriod
from apps.CORE.exceptions import RateLimitError
from apps.CORE.helpers import utc_now
from loggers import get_logger

__all__ = (
    "Rate",
    "BaseRedisRateLimiter",
    "FixedWindowRateLimiter",
    "SlidingWindowRateLimiter",
    "TokenBucketRateLimiter",
)

logger = get_logger(name=__name__)


class Rate:
    def __init__(self, number: int, period: RatePeriod) -> None:
        self._number = number
        self._period = period

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(number={self.number}, period="{self.period}")'

    def __str__(self) -> str:
        return f"{self.number} per {self.period.value.removesuffix('s')}"

    @property
    def number(self) -> int:
        return self._number

    @property
    def period(self) -> RatePeriod:
        return self._period

    @functools.cached_property
    def window_period(self) -> typing.Literal["second", "minute", "hour", "day", "week"]:
        match self.period:
            case RatePeriod.SECOND:
                return "second"
            case RatePeriod.MINUTE:
                return "minute"
            case RatePeriod.HOUR:
                return "hour"
            case RatePeriod.DAY:
                return "day"
            case RatePeriod.WEEK:
                return "week"

    @functools.cached_property
    def seconds(self) -> int:
        match self.period:
            case RatePeriod.SECOND:
                return 1
            case RatePeriod.MINUTE:
                return 60
            case RatePeriod.HOUR:
                return 60 * 60
            case RatePeriod.DAY:
                return 60 * 60 * 24
            case RatePeriod.WEEK:
                return 60 * 60 * 24 * 7

    @functools.cached_property
    def milliseconds(self) -> int:
        return self.seconds * 1000

    @functools.cached_property
    def headers(self) -> dict[str, str]:
        return {
            "RateLimit-Limit": f"{self.number}",
            "RateLimit-Policy": f"{self.number};w={self.seconds}",
        }


class BaseRedisRateLimiter(abc.ABC):
    def __init__(self, rate: Rate, key_prefix: str = "limiter") -> None:
        self._rate = rate
        self._key_prefix = key_prefix

    @abc.abstractmethod
    async def __call__(
        self, *, request: Request, response: Response, redis_client: aioredis.Redis = Depends(get_redis)
    ) -> None:
        raise NotImplementedError

    @property
    def rate(self) -> Rate:
        return self._rate

    @property
    def key_prefix(self) -> str:
        return self._key_prefix

    def key(self, request: Request, now: pendulum.DateTime, previous: bool = False) -> str:
        """Construct key for Redis.

        e.g. key="limiter:/api/v1/login/:127.0.0.1:2023-03-12T13:32:00+00:00:minute:5"

        Args:
            request (Request): FastAPI Request instance.
            now (pendulum.DateTime): DateTime instance from pendulum package.
            previous (bool): Select previous windows instead of current.

        Returns:
            (str): Unique key for Redis
        """
        window_ts = (
            int(self.previous_window_start(now=now).timestamp())
            if previous
            else int(self.current_window_start(now=now).timestamp())
        )
        return (
            f"{self.key_prefix}:{request.url.path}:{self.get_user_id_or_ip(request=request)}:"
            f"{window_ts}:{self.rate.window_period}:{self.rate.number}"
        )

    @staticmethod
    def get_user_id_or_ip(request: Request) -> str:
        try:
            user_id_or_ip = request.user.id
        except AttributeError:
            user_id_or_ip = request.client.host
        return user_id_or_ip

    def now(self) -> pendulum.DateTime:
        return pendulum.instance(dt=utc_now())

    def previous_window_start(self, now: pendulum.DateTime) -> pendulum.DateTime:
        return self.current_window_start(now=now) - datetime.timedelta(seconds=self.rate.seconds)

    def current_window_start(self, now: pendulum.DateTime) -> pendulum.DateTime:
        return now.start_of(unit=self.rate.window_period)

    def next_window_start(self, now: pendulum.DateTime) -> pendulum.DateTime:
        return self.current_window_start(now=now) + datetime.timedelta(seconds=self.rate.seconds)

    def expiration(self, now: pendulum.DateTime) -> pendulum.Period:
        return self.next_window_start(now=now) - now


class FixedWindowRateLimiter(BaseRedisRateLimiter):
    async def __call__(
        self, *, request: Request, response: Response, redis_client: aioredis.Redis = Depends(get_redis)
    ) -> None:
        """FastAPI "Depends" compatibility method, to check User's quotas.

        Args:
            request (Request): FastAPI Request instance.
            response (Response): FastAPI Response instance.
            redis_client (aioredis.Redis): Async client instance for Redis.

        Raises:
            RateLimitExceeded: User exceed his/her quotas for this API.

        Returns:
            None: All is ok, request handling proceed.
        """
        # https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
        now = self.now()
        key = self.key(request=request, now=now)

        # === Redis logic starts ===
        counter: int = await redis_client.incr(name=key)
        expiration = self.expiration(now=now)
        if counter == 1:
            await redis_client.expire(name=key, time=expiration)
        # === Redis logic ends ===

        rate_limit_headers = self.get_and_update_headers(
            request=request,
            response=response,
            hits=counter,
            next_reset_in_seconds=expiration,
            next_window_start=self.next_window_start(now=now),
        )
        if counter > self.rate.number:
            raise RateLimitError(
                message=f"Request limit exceeded for this quota: '{self._rate}'.",
                headers=rate_limit_headers,
            )

    def get_and_update_headers(
        self,
        *,
        request: Request,
        response: Response,
        hits: int,
        next_reset_in_seconds: pendulum.Period,
        next_window_start: pendulum.datetime,
    ) -> dict[str, str]:
        hits_remaining = val if (val := self.rate.number - hits) >= 0 else 0
        result_header = self.rate.headers | {
            "RateLimit-Policy": f'{self.rate.number};w={self.rate.seconds};comment="fixed window"',
            "RateLimit-Remaining": f"{hits_remaining}",
            "Location": request.url.path,
        }
        if not hits_remaining:
            result_header |= {
                "RateLimit-Reset": f"{next_reset_in_seconds.seconds}",
                # Date and time (e.g. Wed, 21 Oct 2015 07:28:00 GMT) OR seconds
                "Retry-After": f"{next_window_start.to_rss_string()}",
            }

        response.headers.update(result_header)
        return result_header


class SlidingWindowRateLimiter(BaseRedisRateLimiter):
    async def __call__(
        self, request: Request, response: Response, redis_client: aioredis.Redis = Depends(get_redis)
    ) -> None:
        now = self.now()
        key = self.key(request=request, now=now)

        # === Redis logic starts ===
        count = int(await redis_client.get(name=key) or 0)
        if int(count) >= self.rate.number:
            rate_limit_headers = self.get_and_update_headers(request=request, response=response, hits=count)
            raise RateLimitError(
                message=f"Request limit exceeded for this quota: '{self.rate}'.", headers=rate_limit_headers
            )

        prev_key = self.key(request=request, now=now, previous=True)
        prev_count = int(await redis_client.get(name=prev_key) or 0)
        prev_percentage = (now.timestamp() % self.rate.seconds) / self.rate.seconds
        weight_count = prev_count * (1 - prev_percentage) + count

        rate_limit_headers = self.get_and_update_headers(
            request=request, response=response, hits=count, weight_count=weight_count
        )
        if weight_count >= self.rate.number:
            raise RateLimitError(
                message=f"Request limit exceeded for this quota, overloaded "
                f"{weight_count:0.3f}/{self.rate.number} for the latest window ({self.rate.window_period}).",
                headers=rate_limit_headers,
            )

        expiration = (self.current_window_start(now=now) + datetime.timedelta(seconds=self.rate.seconds * 2)) - now
        pipe = redis_client.pipeline(transaction=False)
        pipe.incr(name=key)
        pipe.expire(name=key, time=expiration.seconds)
        await pipe.execute()
        # === Redis Logic ends ===

    def get_and_update_headers(
        self,
        *,
        request: Request,
        response: Response,
        hits: int,
        weight_count: float = None,
    ) -> dict[str, str]:
        if weight_count is not None:
            remaining = int(self.rate.number - weight_count)
            rate_limit_remaining = {
                "RateLimit-Remaining": f'{remaining};comment="flood weight={weight_count:0.3f}/{self.rate.number}"'
            }
        else:
            remaining = val if (val := self.rate.number - hits - 1) >= 0 else 0
            rate_limit_remaining = {"RateLimit-Remaining": f'{remaining};comment="exceeded quota by count."'}

        result_headers = (
            self.rate.headers
            | {
                "RateLimit-Policy": f'{self.rate.number};w={self.rate.seconds};comment="sliding window"',
                "Location": request.url.path,
            }
            | rate_limit_remaining
        )

        response.headers.update(result_headers)
        return result_headers


class TokenBucketRateLimiter(BaseRedisRateLimiter):
    async def __call__(
        self, request: Request, response: Response, redis_client: aioredis.Redis = Depends(get_redis)
    ) -> None:
        now = self.now()
        key = self.key(request=request, now=now)

        # === Redis Logic starts ===
        data: dict[str, str] = await redis_client.hgetall(name=key)
        latest_reset_time = data.get(
            "latest_reset_time", (now - datetime.timedelta(seconds=self.rate.seconds)).timestamp()
        )
        if (now - pendulum.from_timestamp(timestamp=int(latest_reset_time))).seconds >= self.rate.seconds:
            await redis_client.hset(
                name=key, mapping={"counter": self.rate.number, "latest_reset_time": int(now.timestamp())}
            )
        else:
            current_counter = int(await redis_client.hget(name=key, key="counter"))
            if current_counter <= 0:
                raise RateLimitError(message=f"Request limit exceeded for this quota: '{self.rate}'.")

        pipe = redis_client.pipeline(transaction=False)
        pipe.hincrby(name=key, key="counter", amount=-1)
        pipe.expire(name=key, time=self.expiration(now=now))
        await pipe.execute()
        # === Redis Logic ends ===
