"""In-process message broker."""
from __future__ import annotations
import asyncio, time
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Message:
    topic: str; payload: Any; seq: int
    timestamp: float = field(default_factory=time.monotonic)
    publisher_id: str = ""

class Topic:
    def __init__(self, name: str, history_depth: int = 100):
        self.name = name; self.history_depth = history_depth
        self._history: list[Message] = []; self._subscribers: list[asyncio.Queue] = []

    async def publish(self, msg: Message):
        self._history.append(msg)
        if len(self._history) > self.history_depth: self._history.pop(0)
        for q in list(self._subscribers):
            try: q.put_nowait(msg)
            except asyncio.QueueFull: pass

    def subscribe(self, maxsize=256) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._subscribers.append(q); return q

    def unsubscribe(self, q):
        if q in self._subscribers: self._subscribers.remove(q)

    @property
    def history(self): return list(self._history)
    @property
    def subscriber_count(self): return len(self._subscribers)

class Broker:
    def __init__(self): self._topics: dict[str,Topic] = {}; self._lock = asyncio.Lock()

    async def get_or_create(self, name: str, history_depth: int = 100) -> Topic:
        async with self._lock:
            if name not in self._topics: self._topics[name] = Topic(name, history_depth)
            return self._topics[name]

    def list_topics(self): return sorted(self._topics.keys())
    def stats(self):
        return {n:{"subscribers":t.subscriber_count,"history_size":len(t.history)} for n,t in self._topics.items()}
