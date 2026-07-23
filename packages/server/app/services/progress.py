"""Redis-backed suite progress events."""

from __future__ import annotations

import json
from typing import Any, cast

import redis
from app.config import Settings


def progress_channel(suite_id: str) -> str:
    return f"agentguard:suite:{suite_id}:progress"


class ProgressPublisher:
    def __init__(self, settings: Settings) -> None:
        self._client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def publish(self, suite_id: str, payload: dict[str, Any]) -> None:
        self._client.publish(progress_channel(suite_id), json.dumps(payload, default=str))

    def subscribe(self, suite_id: str) -> redis.client.PubSub:
        pubsub = cast(
            "redis.client.PubSub",
            self._client.pubsub(ignore_subscribe_messages=True),  # type: ignore[no-untyped-call]
        )
        pubsub.subscribe(progress_channel(suite_id))  # type: ignore[no-untyped-call]
        return pubsub
