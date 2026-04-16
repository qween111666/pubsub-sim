# pubsub-sim

**Async publish/subscribe simulator with configurable rate control, message history, and CSV logging.**

A lightweight in-process pub/sub system built on Python `asyncio`.
Designed to simulate real-time data streaming scenarios — concurrent publishers
at different Hz rates, topic-based routing, history retention, and subscriber callbacks.

---

## Features

- **Topic-based routing** — publishers and subscribers are decoupled through named topics
- **Rate control** — publish at any Hz (1 Hz heartbeat → 200 Hz high-rate telemetry, concurrent)
- **Message history** — configurable depth per topic, queryable at any time
- **CSV logging** — subscribers can log all received messages to disk automatically
- **Non-blocking delivery** — slow subscribers drop messages (bounded per-subscriber queue) rather than blocking publishers
- **Interactive CLI** — test pub/sub live without writing code
- **Zero dependencies** — pure Python `asyncio`, no external brokers

---

## Install

```bash
pip install -r requirements.txt   # just pytest for tests; no runtime deps
```

---

## Interactive CLI

```bash
python -m pubsub_sim
```

```
pubsub-sim interactive console
Type "help" for commands.

>> pub sensor/temperature 25.0 --hz 10
Publishing to 'sensor/temperature' at 10 Hz (value=25.0)

>> sub sensor/temperature
Subscribed to 'sensor/temperature'
  <- [sensor/temperature] seq=0 | 25.0
  <- [sensor/temperature] seq=1 | 25.0
  ...

>> topics
  > sensor/temperature           subs=1  history=10

>> history sensor/temperature 5
  seq=5 | 25.0
  seq=6 | 25.0
  ...

>> stop sensor/temperature
>> quit
```

---

## Python API

### Basic send/receive

```python
import asyncio
from pubsub_sim import Broker, Publisher, Subscriber

async def main():
    broker = Broker()

    received = []
    sub = Subscriber(broker, "sensors/imu", on_message=received.append)
    await sub.start()

    pub = Publisher(broker, "sensors/imu", hz=100.0)
    await pub.start_periodic(value_or_gen=0.0)

    await asyncio.sleep(1.0)   # collect for 1 second

    await pub.stop()
    await sub.stop()
    print(f"Received {sub.count} messages in 1s at 100 Hz")

asyncio.run(main())
```

### Concurrent multi-rate publishers

```python
import asyncio
from pubsub_sim import Broker, Publisher, Subscriber
from pubsub_sim.publisher import _sweep_generator

async def main():
    broker = Broker()

    pub_fast  = Publisher(broker, "data/high-rate",   hz=200.0)
    pub_slow  = Publisher(broker, "data/status",      hz=1.0)

    sub = Subscriber(broker, "data/high-rate",
                     on_message=lambda m: print(f"[{m.topic}] {m.payload}"))
    await sub.start()

    await pub_fast.start_periodic(_sweep_generator(0, 360, 1))   # angle sweep
    await pub_slow.start_periodic("OK")

    await asyncio.sleep(2.0)

    await pub_fast.stop()
    await pub_slow.stop()
    await sub.stop()

asyncio.run(main())
```

### CSV logging

```python
sub = Subscriber(
    broker, "sensors/temperature",
    log_to_csv="temperature_log.csv",
)
await sub.start()
# ... run ...
# CSV columns: timestamp, topic, seq, publisher_id, payload
```

---

## Architecture

```
Publisher --publish(msg)--> Topic --dispatch--> Subscriber queue --> callback
                               |
                               +-- history[]  (ring buffer, configurable depth)

Multiple publishers -> same topic (fan-in)
One publisher      -> multiple subscribers (fan-out)
```

**Message fields:**

| Field | Type | Description |
|---|---|---|
| `topic` | `str` | Topic name |
| `payload` | `Any` | Message content |
| `seq` | `int` | Per-publisher sequence number |
| `timestamp` | `float` | `time.monotonic()` at publish time |
| `publisher_id` | `str` | Publisher identifier |

---

## Run tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## License

MIT
