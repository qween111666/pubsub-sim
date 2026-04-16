"""
Example: three publishers at different rates feeding one subscriber.
Demonstrates the same concurrent multi-rate pattern used in production
validation systems (e.g. 100 Hz telemetry + 10 Hz status + 1 Hz heartbeat).
"""

import asyncio
import time

from pubsub_sim import Broker, Publisher, Subscriber
from pubsub_sim.publisher import _sweep_generator


async def main():
    broker = Broker()

    # Three publishers at different rates
    pub_fast   = Publisher(broker, "sensor/temperature", hz=100.0, publisher_id="fast")
    pub_medium = Publisher(broker, "sensor/pressure",    hz=10.0,  publisher_id="medium")
    pub_slow   = Publisher(broker, "system/heartbeat",   hz=1.0,   publisher_id="slow")

    received = {"temperature": 0, "pressure": 0, "heartbeat": 0}

    def on_msg(msg):
        key = msg.topic.split("/")[1]
        received[key] += 1

    sub  = Subscriber(broker, "sensor/temperature", on_message=on_msg)
    sub2 = Subscriber(broker, "sensor/pressure",    on_message=on_msg)
    sub3 = Subscriber(broker, "system/heartbeat",   on_message=on_msg)

    await sub.start()
    await sub2.start()
    await sub3.start()

    # Start publishers -- sweep values
    await pub_fast.start_periodic(_sweep_generator(0.0, 100.0, 0.5))
    await pub_medium.start_periodic(_sweep_generator(900.0, 1100.0, 5.0))
    await pub_slow.start_periodic(1)   # constant heartbeat

    print("Running for 3 seconds...")
    await asyncio.sleep(3.0)

    await pub_fast.stop()
    await pub_medium.stop()
    await pub_slow.stop()
    await sub.stop()
    await sub2.stop()
    await sub3.stop()

    print(f"\nReceived in 3s:")
    print(f"  temperature (100 Hz): {received['temperature']} messages")
    print(f"  pressure    ( 10 Hz): {received['pressure']} messages")
    print(f"  heartbeat   (  1 Hz): {received['heartbeat']} messages")

    # Verify approximate rates
    assert received["temperature"] > 200, "Expected ~300 temperature messages"
    assert received["pressure"] > 20,    "Expected ~30 pressure messages"
    assert received["heartbeat"] >= 2,   "Expected ~3 heartbeat messages"
    print("\nAll rate assertions passed ✓")


if __name__ == "__main__":
    asyncio.run(main())
