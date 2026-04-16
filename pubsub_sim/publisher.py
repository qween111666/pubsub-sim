"""Publisher — sends messages to a topic at configurable Hz."""
from __future__ import annotations
import asyncio, time
from typing import Any, Iterator, Optional
from .broker import Broker, Message

def _sweep_generator(lo, hi, step=1.0):
    v, d = lo, step
    while True:
        yield round(v, 6); v += d
        if v >= hi: d = -step
        elif v <= lo: d = step

class Publisher:
    def __init__(self, broker: Broker, topic: str, publisher_id="pub", hz=1.0, history_depth=100):
        self.broker=broker; self.topic_name=topic; self.publisher_id=publisher_id
        self.hz=hz; self.history_depth=history_depth; self._seq=0
        self._running=False; self._task=None

    async def send(self, payload: Any) -> Message:
        t = await self.broker.get_or_create(self.topic_name, self.history_depth)
        msg = Message(self.topic_name, payload, self._seq, publisher_id=self.publisher_id)
        self._seq += 1; await t.publish(msg); return msg

    async def start_periodic(self, value_or_gen, count=None):
        if self._running: raise RuntimeError("already running")
        gen = self._make_gen(value_or_gen); self._running = True; interval = 1.0/self.hz
        async def _loop():
            sent = 0
            try:
                while self._running:
                    t0 = time.monotonic(); await self.send(next(gen)); sent += 1
                    if count is not None and sent >= count: break
                    await asyncio.sleep(max(0.0, interval-(time.monotonic()-t0)))
            finally: self._running = False
        self._task = asyncio.create_task(_loop())

    async def stop(self):
        self._running = False
        if self._task: await self._task; self._task = None

    @property
    def is_running(self): return self._running

    @staticmethod
    def _make_gen(v):
        if hasattr(v,"__next__"): return v
        if callable(v):
            def g():
                while True: yield v()
            return g()
        def s():
            while True: yield v
        return s()
