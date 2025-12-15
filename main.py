import asyncio
from scheduled_callback import ScheduledCallback, create_secret_strings
from load_callback_configs import load_callback_configs
from timewheel import TimeWheel
import psycopg
import os

if __name__ == "__main__":
    stop = asyncio.Event()

    database_string = (
        f"postgresql://{os.getenv("POSTGRES_USER")}"
        f":{os.getenv("POSTGRES_PASSWORD")}"
        "@localhost:5432/postgres"
    )

    async def main():
        conn = psycopg.connect(database_string)
        callbacks = [ScheduledCallback(c) for c in load_callback_configs(conn)]
        
        for c in callbacks:
            config = c.config
            _, refresh_secret = create_secret_strings(config)
            refresh_token = await c.secret_client.get_secret(refresh_secret)
            if not refresh_token:
                print(f"[!! WARNING !!] Missing refresh token for: {c.config}\n")
                raise RuntimeError(f"Missing refresh tokens for: {c.config}")
            c.config.body = c.update_fn(c.config.body, "refresh_token", refresh_token)
            print(c.config.body)

        wheel = TimeWheel(base_tick=1.0, wheels=6, slots=10)
        list(map(wheel.schedule, callbacks))
        wheel.start()
        await stop.wait()

    asyncio.run(main())