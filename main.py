import asyncio
import time
from constants import *
from scheduled_callback import ScheduledCallback
from global_variables import wheel, queue
from database_connection import load_config_from_database
import httpx
import re

async def worker():
    """ Execute sheduled callbacks from queue and reschedule new ones in wheel. """
    while True:
        sc = await queue.get()
        print((
            f"Executing for: {sc.auth_config.customer_alias} "
            f"with deadline: {sc.scheduled_tick}"
        ))
        try:
            # Update the fresh and access tokens 
            await sc.callback()

            # Compute the new deadline
            new_scheduled_tick = (
                sc.scheduled_tick + sc.auth_config.expires_in - TIME_MARGIN
            ) % TIME_WHEEL_SIZE

            # Update the deadline 
            sc.scheduled_tick = new_scheduled_tick

            # Add the scheduled callback to the wheel again
            wheel[new_scheduled_tick].append(sc) 

            print(f"Scheduled new callback for tick {new_scheduled_tick}")

        finally:
            queue.task_done()

# All data that the callback needs to refresh a token
async def queue_wheel_slot(t: int):
        if wheel[t]:
            print(f"Queueing {len(wheel[t])} callbacks..")
        for sc in wheel[t]:
            await queue.put(sc)
        wheel[t] = []

async def tick_loop():
    """ Move scheduled callbacks from wheel onto queue. """
    t = 0
    next_tick_time = time.monotonic() + TICK_INTERVAL

    while True:
        print(f'\n--- tick {t} ---')
        await queue_wheel_slot(t)

        now = time.monotonic()
        diff = next_tick_time - now
        if diff > 0:
            await asyncio.sleep(diff)

        t = (t + 1) %  TIME_WHEEL_SIZE
        next_tick_time += TICK_INTERVAL


# For testing
async def initial_call(url: str, client_id: str) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    body = f'''
    {{
        "grant_type": "client_credentials",
        "client_id": "{client_id}",
        "client_secret": "test"
    }}
    '''
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=url,
            headers=headers,
            content=body
        )
    return response.json()


async def main():
    for _ in range(NUM_WORKERS):
        asyncio.create_task(worker())

    # Enque an initial callback to start the process
    configs = load_config_from_database()

    # Create a scheduled callback for each config
    for c in configs:
        scheduled_tick = c.expires_in - TIME_MARGIN
        print(f"Scheduling for: {c.customer_alias}")
        sc = ScheduledCallback(c, scheduled_tick)
        # Use customer alias as client_id for tracking
        data = await initial_call(sc.auth_config.url, sc.auth_config.customer_alias)
        sc.auth_config.body = re.sub(
            pattern=r"refresh_token=[^&]*",
            repl=f"refresh_token={data["refresh_token"]}",
            string=sc.auth_config.body
        )
        wheel[scheduled_tick].append(sc) 

    await tick_loop()


if __name__ == "__main__":
    asyncio.run(main())