import asyncio
import time
from constants import *
from httpx import Response
from scheduled_callback import ScheduledCallback, callback
from global_variables import wheel, queue, INITIAL_ARGS

# Send an intial call to the authorization server
url = "http://127.0.0.1:8000/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": "Basic Y2xpZW50MTIzOnNlY3JldDEyMw=="
}
body = {
    "grant_type" : "password",
    "username" : "test",
    "password" : "123"
}
response = asyncio.run(callback(url, headers, body))

initial_refresh_token = response.json()["refresh_token"]
INITIAL_ARGS["body"]["refresh_token"] = initial_refresh_token

async def worker():
    """ Execute sheduled callbacks from queue and reschedule new ones in wheel. """
    while True:
        sc = await queue.get()
        print(f"Executing callback for deadline: {sc.deadline_tick}..")
        try:
            # Get a response from the refresh endpoint
            response: Response = await sc.callback(
                sc.args['url'],
                sc.args['headers'],
                sc.args['body']
            )
            if response:
                print("Got new token from server..")
            data = response.json()

            # Update the args with the new refresh token
            sc.args["body"]["refresh_token"] = data["refresh_token"]

            # Compute the new deadline
            new_deadline_tick = (
                sc.deadline_tick + sc.ticks_to_deadline - TIME_MARGIN
            ) % TIME_WHEEL_SIZE

            # Update the deadline 
            sc.deadline_tick = new_deadline_tick

            # Add the scheduled callback to the wheel again
            wheel[new_deadline_tick].append(sc) 

            print(f"scheduled new callback for tick {new_deadline_tick}")

        finally:
            queue.task_done()

# All data that the callback needs to refresh a token
async def queue_wheel_slot(t: int):
        print(f"Queueing wheel slot for tick: {t}")
        for sc in wheel[t]:
            print("Queueing new callback..")  
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

async def main():
    for _ in range(NUM_WORKERS):
        asyncio.create_task(worker())
    # Enque an initial callback to start the process
    initial_t = TICKS_TO_DEADLINE - TIME_MARGIN
    sc = ScheduledCallback(
        callback, INITIAL_ARGS, initial_t, TICKS_TO_DEADLINE 
    ) 
    wheel[initial_t].append(sc) 
    await tick_loop()


if __name__ == "__main__":
    asyncio.run(main())