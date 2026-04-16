import asyncio, pytest
from pubsub_sim import Broker, Publisher, Subscriber

@pytest.mark.asyncio
async def test_basic():
    b=Broker(); recv=[]
    s=Subscriber(b,"t",on_message=recv.append); await s.start()
    p=Publisher(b,"t"); await p.send("hello"); await asyncio.sleep(0.05); await s.stop()
    assert len(recv)==1 and recv[0].payload=="hello"

@pytest.mark.asyncio
async def test_rate():
    b=Broker(); s=Subscriber(b,"r"); await s.start()
    p=Publisher(b,"r",hz=50.0); await p.start_periodic(1.0,count=20)
    await asyncio.sleep(0.8); await s.stop()
    assert 15 < s.count <= 20, f"got {s.count}"

@pytest.mark.asyncio
async def test_fanout():
    b=Broker(); c=[0,0]
    s1=Subscriber(b,"x",on_message=lambda _:c.__setitem__(0,c[0]+1)); await s1.start()
    s2=Subscriber(b,"x",on_message=lambda _:c.__setitem__(1,c[1]+1)); await s2.start()
    p=Publisher(b,"x")
    for _ in range(5): await p.send("m")
    await asyncio.sleep(0.05); await s1.stop(); await s2.stop()
    assert c==[5,5]

@pytest.mark.asyncio
async def test_history():
    b=Broker(); p=Publisher(b,"h",history_depth=5)
    for i in range(10): await p.send(i)
    t=await b.get_or_create("h")
    assert len(t.history)==5 and t.history[-1].payload==9

@pytest.mark.asyncio
async def test_seq_numbers():
    b=Broker(); recv=[]; s=Subscriber(b,"s",on_message=recv.append); await s.start()
    p=Publisher(b,"s")
    for _ in range(5): await p.send("x")
    await asyncio.sleep(0.05); await s.stop()
    assert [m.seq for m in recv]==list(range(5))
