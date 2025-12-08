import psycopg
import os
from callback_config import CallbackConfig
import dotenv
dotenv.load_dotenv(".env")

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
    "expires_in_ticks"
]

def load_config_from_database():
    conn = psycopg.connect(
        f"postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:5432/postgres",
    )
    # Load configs
    with conn.cursor() as cur:
        query = """
        SELECT 
            scale, seconds_per_tick, c.id, url, headers, body, expires_in_seconds, time_wheel_scale, module_alias, system_alias, customer_alias, instance_alias,
            seconds_per_tick * expires_in_seconds as expires_in_ticks
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

    return configs