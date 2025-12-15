import psycopg
from psycopg.rows import TupleRow
from callback_config import CallbackConfig
import dotenv

dotenv.load_dotenv(".env")
    
def load_callback_configs(conn: psycopg.Connection[TupleRow]):
    columns = [
        "id", "url", "headers", "body", "expires_in_seconds", "module_alias",
        "system_alias", "customer_alias", "instance_alias", "refresh_token_keys",
        "access_token_keys"
    ]
    with conn.cursor() as cur:
        query = """
            SELECT 
                id, url, headers, body, expires_in_seconds, module_alias, system_alias,
                customer_alias, instance_alias, refresh_token_keys, access_token_keys
            FROM auth.config
        """
        cur.execute(query)
        rows = cur.fetchall()
        configs: list[CallbackConfig] = [
            CallbackConfig.model_validate(dict(zip(columns, row)))
            for row in rows
        ]
    return configs