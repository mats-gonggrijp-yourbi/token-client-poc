# type: ignore
import random
import string
import psycopg

# =========================
# Configuration
# =========================
DB_CONFIG = { # type: ignore
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
}

ROWS_TO_INSERT = 5          
EXPIRES_MIN = 5             
EXPIRES_MAX = 30            

# =========================
# Helpers
# =========================
def random_string(length: int = 5) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_json_array_string() -> str:
    # produces e.g. ["Ab3Xy"]
    return f'["{random_string()}"]'


# =========================
# Insert logic
# =========================
def insert_test_rows():
    sql = """
        INSERT INTO auth.config (
            url,
            headers,
            body,
            expires_in_seconds,
            module_alias,
            system_alias,
            customer_alias,
            instance_alias,
            refresh_token_keys,
            access_token_keys
        )
        VALUES (
            %(url)s,
            %(headers)s,
            %(body)s,
            %(expires_in_seconds)s,
            %(module_alias)s,
            %(system_alias)s,
            %(customer_alias)s,
            %(instance_alias)s,
            %(refresh_token_keys)s,
            %(access_token_keys)s
        );
    """

    rows = []
    for _ in range(ROWS_TO_INSERT):
        rows.append( # type: ignore
            {
                "url": "http://127.0.0.1:8000/token",
                "headers": '{"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Bearer ..."}',
                "body": "grant_type=refresh_token&refresh_token=NULL",
                "expires_in_seconds": random.randint(EXPIRES_MIN, EXPIRES_MAX),
                "module_alias": random_string(),
                "system_alias": random_string(),
                "customer_alias": random_string(),
                "instance_alias": random_string(),
                "refresh_token_keys": random_json_array_string(),
                "access_token_keys": random_json_array_string(),
            }
        )

    with psycopg.connect(**DB_CONFIG) as conn: 
        with conn.cursor() as cur:
            cur.executemany(sql, rows)

        conn.commit()

    print(f"Inserted {ROWS_TO_INSERT} rows into auth.config")


if __name__ == "__main__":
    insert_test_rows()
