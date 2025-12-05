import psycopg
import os
from callback_config import CallbackConfig
import dotenv
dotenv.load_dotenv(".env")

columns = [
    "id", "url", "headers", "body", "expires_in",
    "module_alias", "system_alias", "customer_alias", "instance_alias"
]

def load_config_from_database():
    conn = psycopg.connect(
        f"postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:5432/postgres",
    )

    # Load configs
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM auth.config")
        rows = cur.fetchall()
        configs: list[CallbackConfig] = [
            CallbackConfig.model_validate(dict(zip(columns, row)))
            for row in rows
        ]

    return configs

