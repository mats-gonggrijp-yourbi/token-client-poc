import asyncio
import time
from scheduled_callback import ScheduledCallback
from database_connection import load_config_from_database
import httpx
from typing import Any
from urllib.parse import parse_qsl, urlencode
import json

TIME_WHEEL_SIZE = 32
TIME_MARGIN = 3
NUM_WORKERS = 1
SECONDS_PER_TICK = 2.0

time_wheel: list[list[ScheduledCallback]] = [[] for _ in range(TIME_WHEEL_SIZE)] 
callback_queue: asyncio.Queue[ScheduledCallback] = asyncio.Queue()

async def worker():
    """ Execute sheduled callbacks from queue and reschedule new ones in wheel. """
    while True:
        sc = await callback_queue.get()
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
            time_wheel[new_scheduled_tick].append(sc) 

            print(f"Scheduled new callback for tick {new_scheduled_tick}")

        finally:
            callback_queue.task_done()


async def queue_wheel_slot(t: int):
        if time_wheel[t]:
            print(f"Queueing {len(time_wheel[t])} callbacks..")
        for sc in time_wheel[t]:
            await callback_queue.put(sc)
        time_wheel[t] = []


async def tick_loop():
    """ Move scheduled callbacks from wheel onto queue. """
    t = 0
    next_tick_time = time.monotonic() + SECONDS_PER_TICK

    while True:
        print(f'\n--- tick {t} ({t * SECONDS_PER_TICK} seconds)---')
        await queue_wheel_slot(t)

        now = time.monotonic()
        diff = next_tick_time - now
        if diff > 0:
            await asyncio.sleep(diff)

        t = (t + 1) %  TIME_WHEEL_SIZE
        next_tick_time += SECONDS_PER_TICK

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


async def update_client_credentials(
        body: dict[str, str],
        scheduled_callback: ScheduledCallback
    ):
    # Add client ID and secret if they are necessary
    if "client_id" in body:
        body["client_id"] = await scheduled_callback.secret_client.get_secret("ClientId")
    if "client_secret" in body:
        body["client_secret"] = await scheduled_callback.secret_client.get_secret("ClientId")


async def main():
    for _ in range(NUM_WORKERS):
        asyncio.create_task(worker())

    # Configs per callback are stored in the database
    configs = load_config_from_database()

    # Create a scheduled callback for each config
    for c in configs:
        scheduled_tick = c.expires_in - TIME_MARGIN
        print(f"Scheduling for: {c.customer_alias}")
        sc = ScheduledCallback(c, scheduled_tick)

        # Get initial refresh token from auth server (this would be manual)
        data = await initial_call(sc.auth_config.url, sc.auth_config.customer_alias)
        rt = data["refresh_token"]
        at = data["access_token"]

        ctype = c.headers["Content-Type"]
        if ctype == "application/x-www-form-urlencoded":
            body = dict(parse_qsl(c.body))
            await update_client_credentials(body, sc)
            body['refresh_token'] = rt
            c.body = urlencode(body)

        elif ctype == "application/json":
            body = json.loads(c.body)
            await update_client_credentials(body, sc)
            body['refresh_token'] = rt
            c.body = json.dumps(body)
        
        else:
            raise RuntimeError(
                "Content-Type must be either json or x-www-url-form-encoded"
            )
        
        # Set the refresh and access tokens in the customer's keyvault
        await sc.secret_client.update_secret("RefreshToken", rt)
        await sc.secret_client.update_secret("AccessToken", at)

        print(sc.auth_config.body)

        # Schedule the callback 
        time_wheel[scheduled_tick].append(sc) 

    print(f"Loaded {len(configs)} configs")

    await tick_loop()


if __name__ == "__main__":
    asyncio.run(main())