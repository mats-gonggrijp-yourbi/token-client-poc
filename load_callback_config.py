import psycopg
import os
from callback_config import CallbackConfig
import dotenv
from timewheel_config import TimeWheelConfig

dotenv.load_dotenv(".env")

conn = psycopg.connect((
    f"postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}"
    "@localhost:5432/postgres"
))

def load_timewheel_configs_from_database() -> dict[str, TimeWheelConfig]:
    columns = ["id", "scale", "size", "seconds_per_tick", "tick_safety_margin", "num_workers"]
    configs: dict[str, TimeWheelConfig] = {}
    with conn.cursor() as cur:
        query = "SELECT  * FROM auth.time_wheels"
        cur.execute(query)
        rows = cur.fetchall()
        for r in rows:
            model = TimeWheelConfig.model_validate(dict(zip(columns, r)))
            configs[model.scale] = model
    return configs

def load_callback_configs_from_database():
    columns = [
        "scale",
        "seconds_per_tick",
        "id",
        "url",
        "headers",
        "body",
        "expires_in_seconds",
        "time_wheel_scale",
        "module_alias",
        "system_alias",
        "customer_alias",
        "instance_alias",
        "wait_time_in_seconds",
        "expires_in_ticks",
        "wait_time_in_ticks"
    ]
    with conn.cursor() as cur:
        query = """
            SELECT 
                scale,
                seconds_per_tick,
                c.id,
                url,
                headers,
                body,
                expires_in_seconds,
                time_wheel_scale,
                module_alias,
                system_alias,
                customer_alias,
                instance_alias,
                wait_time_in_seconds,
                FLOOR(expires_in_seconds::NUMERIC / seconds_per_tick::NUMERIC) as expires_in_ticks,
                CEILING(wait_time_in_seconds::NUMERIC / seconds_per_tick::NUMERIC) as wait_time_in_ticks
            FROM auth.time_wheels AS tw
            JOIN auth.config AS c
            ON tw.scale = c.time_wheel_scale;
        """
        cur.execute(query)
        rows = cur.fetchall()
        configs: list[CallbackConfig] = [
            CallbackConfig.model_validate(dict(zip(columns, row)))
            for row in rows
        ]

        for c in configs:
            print(c.model_dump_json(indent=2), '\n\n')

    return configs


load_callback_configs_from_database()