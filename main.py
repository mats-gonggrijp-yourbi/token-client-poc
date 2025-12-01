import asyncio
import time
from dataclasses import dataclass
from typing import Callable, Awaitable
import httpx
from typing import Any
from config import *
from httpx import Response 

@dataclass
class ScheduledCallback:
    callback: Callable[[], Awaitable[Any]]
    args: dict[Any, Any]
    tick: int
    deadline: int

async def callback(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any]
):
    async with httpx.AsyncClient() as client:
        print("headers ", headers, "\n", "body ", body, "\n")

        if headers["Content-Type"] == 'application/json':
            return await client.post(url, headers=headers, json=body)
    
        elif headers["Content-Type"] == 'application/x-www-form-urlencoded':
            return await client.post(url, headers=headers, data=body)

        raise RuntimeError

wheel: list[list[ScheduledCallback]] = [[] for _ in range(TIME_WHEEL_SIZE)] 
queue: asyncio.Queue[ScheduledCallback] = asyncio.Queue()

# Send an intial call to the authorization server
response = asyncio.run(callback(
        "http://127.0.0.1:8000/token",
        {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic Y2xpZW50MTIzOnNlY3JldDEyMw=="
        },
        {
            "grant_type" : "password",
            "username" : "test",
            "password" : "123"
        }
))

initial_refresh_token = response.json()["refresh_token"]

# All data that the callback needs to refresh a token
args1: dict[Any, Any] = {
    "url" : "http://127.0.0.1:8000/token",
    "headers" : {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic Y2xpZW50MTIzOnNlY3JldDEyMw=="
    },
    "body" : {
        "grant_type" : "refresh_token",
        "refresh_token" : initial_refresh_token
    }
}

args2: dict[Any, Any] = {
    "url" : "http://127.0.0.1:8000/token",
    "headers" : {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic Y2xpZW50MTIzOnNlY3JldDEyMw=="
    },
    "body" : {
        "grant_type" : "refresh_token",
        "refresh_token" : initial_refresh_token
    }
}


async def tick_loop():
    """ Move scheduled callbacks from wheel onto queue. """
    t = 0
    next_tick = time.monotonic()

    while True:
        print(f"\n----------- tick {t} -----------")

        # Move callbacks scheduled for this tick to worker queue
        for sc in wheel[t]:  
            await queue.put(sc)
        wheel[t] = []

        now = time.monotonic()
        diff = next_tick - now
        if diff > 0:
            await asyncio.sleep(diff)

        t = (t + 1) % TIME_WHEEL_SIZE
        next_tick += TICK_INTERVAL


async def worker():
    """ Execute sheduled callbacks from queue and reschedule new ones in wheel. """
    while True:
        sc = await queue.get()
        print(f"executing callback for tick {sc.tick}")
        try:
            # Get a response from the refresh endpoint
            response: Response = await sc.callback(**sc.args)
            print("response ", response)
            data = response.json()
            insert_t = (sc.tick + sc.deadline - TIME_MARGIN) % TIME_WHEEL_SIZE

            # Schedule another request with the new refresh token from the response
            args1["body"]["refresh_token"] = data["refresh_token"]
            sc1 = ScheduledCallback(callback, args1, insert_t, 8) # type: ignore
            wheel[insert_t].append(sc1) 
            print(f"scheduled new callback for tick {insert_t}")

        finally:
            queue.task_done()


async def main():
    for _ in range(NUM_WORKERS):
        asyncio.create_task(worker())

    # Initial tick should be a little bit offset from the start
    tick = TIME_MARGIN + 1

    # Enque an initial callback to start the process
    sc1 = ScheduledCallback(callback, args1, tick, 8) # type: ignore
    # sc2 = ScheduledCallback(callback, args2, tick, 12) # type: ignore

    wheel[tick].append(sc1) 
    await tick_loop()


if __name__ == "__main__":
    asyncio.run(main())