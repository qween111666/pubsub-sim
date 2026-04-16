"""Subscriber — receives messages and dispatches to callback, optionally logs to CSV."""
from __future__ import annotations
import asyncio, csv
from pathlib import Path
from typing import Callable, Optional
from .broker import Broker, Message

class Subscriber:
    def __init__(self, broker: Broker, topic: str, subscriber_id="sub",
                 on_message: Optional[Callable]=None, log_to_csv=None, queue_size=256):
        self.broker=broker; self.topic_name=topic; self.subscriber_id=subscriber_id
        self.on_message=on_message or (lambda _: None); self.log_path=Path(log_to_csv) if log_to_csv else None
        self._queue=None; self._task=None; self._running=False
        self._received=[]; self._queue_size=queue_size; self._csv_writer=None; self._csv_file=None

    async def start(self):
        t = await self.broker.get_or_create(self.topic_name)
        self._queue = t.subscribe(self._queue_size); self._running = True
        if self.log_path:
            self._csv_file = open(self.log_path,"w",newline=""); self._csv_writer=csv.writer(self._csv_file)
            self._csv_writer.writerow(["timestamp","topic","seq","publisher_id","payload"])
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
        if self._csv_file: self._csv_file.close()
        t = await self.broker.get_or_create(self.topic_name)
        if self._queue: t.unsubscribe(self._queue)

    async def _loop(self):
        while self._running:
            try: msg: Message = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except asyncio.TimeoutError: continue
            except asyncio.CancelledError: break
            self._received.append(msg)
            if self._csv_writer:
                self._csv_writer.writerow([msg.timestamp,msg.topic,msg.seq,msg.publisher_id,msg.payload])
                self._csv_file.flush()
            try: self.on_message(msg)
            except Exception as e: print(f"[{self.subscriber_id}] callback error: {e}")

    @property
    def messages(self): return list(self._received)
    @property
    def count(self): return len(self._received)
    @property
    def is_running(self): return self._running
