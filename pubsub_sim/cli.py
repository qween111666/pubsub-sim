"""Interactive CLI: python -m pubsub_sim"""
import asyncio, shlex, sys
from .broker import Broker
from .publisher import Publisher
from .subscriber import Subscriber

async def run_cli():
    broker=Broker(); publishers={}; subscribers={}
    print("pubsub-sim  |  type \'help\' for commands\n")
    def _print(msg): print(f"  <- [{msg.topic}] seq={msg.seq} | {msg.payload}")
    while True:
        try: raw = await asyncio.get_event_loop().run_in_executor(None, lambda: input(">> "))
        except (EOFError,KeyboardInterrupt): break
        parts = shlex.split(raw.strip())
        if not parts: continue
        cmd,*args = parts
        if cmd=="pub":
            if len(args)<2: print("pub <topic> <value> [--hz N]"); continue
            topic,value=args[0],args[1]; hz=1.0
            if "--hz" in args:
                try: hz=float(args[args.index("--hz")+1])
                except: print("bad hz"); continue
            try: val=float(value)
            except: val=value
            pub=Publisher(broker,topic,publisher_id=f"cli-{topic}",hz=hz)
            publishers[topic]=pub; await pub.start_periodic(val)
            print(f"Publishing \'{topic}\' @ {hz}Hz value={val}")
        elif cmd=="stop":
            if args and args[0] in publishers: await publishers[args[0]].stop(); print(f"Stopped \'{args[0]}\'")
        elif cmd=="sub":
            if not args: print("sub <topic>"); continue
            t=args[0]; sub=Subscriber(broker,t,on_message=_print,subscriber_id=f"sub-{t}")
            subscribers[t]=sub; await sub.start(); print(f"Subscribed \'{t}\'")
        elif cmd=="unsub":
            if args and args[0] in subscribers: await subscribers[args[0]].stop(); print(f"Unsubscribed \'{args[0]}\'")
        elif cmd=="send":
            if len(args)<2: print("send <topic> <value>"); continue
            try: val=float(args[1])
            except: val=args[1]
            await Publisher(broker,args[0],publisher_id="oneshot").send(val); print(f"Sent {val\!r} -> \'{args[0]}\'")
        elif cmd=="topics":
            for n,s in (broker.stats() or {}).items():
                r=">" if n in publishers and publishers[n].is_running else " "
                print(f"  {r} {n:<30} subs={s[\'subscribers\']}  hist={s[\'history_size\']}")
        elif cmd=="history":
            if not args: print("history <topic> [n]"); continue
            t=await broker.get_or_create(args[0]); n=int(args[1]) if len(args)>1 else 10
            for m in t.history[-n:]: print(f"  seq={m.seq} | {m.payload}")
        elif cmd in ("quit","exit","q"): break
        elif cmd=="help": print(__doc__ or "pub sub unsub stop send topics history quit")
        else: print(f"unknown: {cmd\!r}")
    for pub in publishers.values():
        if pub.is_running: await pub.stop()
    for sub in subscribers.values():
        if sub.is_running: await sub.stop()
    print("bye")

def main(): asyncio.run(run_cli())
