import psycopg
import random

# ---------------------------------------------
# CONFIGURATION CONSTANTS
# ---------------------------------------------
NUM_ROWS_PER_SCALE = {
    '1-5 seconds': 3,
    '6-60 seconds': 3,
}
MIN_EXPIRY_VALUES = {
    '1-5 seconds': 1,
    '6-60 seconds': 6,
}
MAX_EXPIRY_VALUES = {
    '1-5 seconds': 5,
    '6-60 seconds': 60,
}
CONN_STRING = "postgresql://postgres:postgres@localhost:5432/postgres"

# ---------------------------------------------
# MAIN INSERT LOGIC
# ---------------------------------------------
def insert_test_data():
    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cur:
            for scale, num_rows in NUM_ROWS_PER_SCALE.items():
                min_expiry = MIN_EXPIRY_VALUES[scale]
                max_expiry = MAX_EXPIRY_VALUES[scale]

                print(f"Inserting {num_rows} entries for scale '{scale}' with range {min_expiry}-{max_expiry}s")

                for i in range(num_rows):
                    expires = random.randint(min_expiry, max_expiry)

                    url = "http://127.0.0.1:8000/token"
                    headers = '{"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Bearer ..."}'
                    body = "grant_type=refresh_token&refresh_token=..."

                    module_alias = "pos"
                    system_alias = "coolsystem"
                    customer_alias = f"random-customer-{scale.replace(' ', '').replace('-', '')}-{i}"
                    instance_alias = f"random-instance-{scale.replace(' ', '').replace('-', '')}-{i}"

                    cur.execute(
                        """
                        INSERT INTO auth.config 
                        (url, headers, body, expires_in_seconds, time_wheel_scale, 
                         module_alias, system_alias, customer_alias, instance_alias, wait_time_in_seconds)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                        """,
                        (
                            url,
                            headers,
                            body,
                            expires,
                            scale,
                            module_alias,
                            system_alias,
                            customer_alias,
                            instance_alias
                        )
                    )

        conn.commit()
        print("\n✔ Done inserting test data!\n")

# ---------------------------------------------
# RUN SCRIPT
# ---------------------------------------------
if __name__ == "__main__":
    insert_test_data()
