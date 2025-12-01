import psycopg
from config import CONFIG 
import os
from typing import Any
import json
from urllib.parse import parse_qsl
import dotenv
dotenv.load_dotenv(".env")

conn = psycopg.connect((
    f"postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}"
    "@localhost:5432/postgres"
))

# Load the config for each token refresh
with conn.cursor() as cur:
    cur.execute("SELECT * FROM auth.config")
    rows = cur.fetchall()
    for r in rows:
        # Last 4 columns: module, system, customer, instance
        composite_id = "/".join(r[len(r) - 4 :])

        # First: id, url, type, method, headers, body, expires_in
        data: dict[str, Any] = {
            "id" : r[0],
            "url" : r[1],
            "type" : r[2],
            "method" : r[3],
            "headers" : json.loads(r[4]),
            "expires_in" : r[6]
        }

        content_type: str = data["headers"]["Content-Type"] 
        if content_type == "application/json":
            data["body"] = json.loads(r[5])

        elif content_type == "application/x-www-form-urlencoded":
            data["body"] = dict(parse_qsl(r[5]))

        # Shared global state for token config
        CONFIG[composite_id] = data

print(CONFIG)