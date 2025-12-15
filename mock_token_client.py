from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import secrets #, time
from typing import Any
from starlette.datastructures import FormData
import asyncio
import psycopg

RESPONSE_TIME = 0.1

app = FastAPI()
# refresh_store: dict[str, dict[Any, Any]] = {
#     "DUMMY VALUE FOR TESTING" : {
#         "owner": "DUMMY" , "issued_at": time.time(), "access_exp": time.time() + 30
#     }
# }

CONN_STRING = "postgresql://postgres:postgres@localhost:5432/postgres"
with psycopg.connect(CONN_STRING) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM auth.config")
        rows = cur.fetchall()
        ids = {next(iter(r)) for r in rows}

late_calls: list[str] = []

def parse_body(data: dict[Any, Any] | FormData) -> dict[Any, Any]:
    if isinstance(data, dict):
        return data
    return dict(data)

def issue_tokens(owner: str) -> dict[str, str | int]:
    access = secrets.token_hex(16)
    refresh = secrets.token_hex(32)
    # refresh_store[refresh] = {"owner": owner, "issued_at": time.time(), "access_exp": time.time() + 30}
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "expires_in": 30}

@app.post("/token")
async def token(req: Request):
    # Mimick realistic server response times 
    await asyncio.sleep(RESPONSE_TIME) 

    body = await req.json() if req.headers.get("Content-Type","").startswith("application/json") else await req.form()
    print(f"Received: {body}")
    body_dict: dict[Any, Any] = parse_body(body)
    grant_type = body_dict.get("grant_type")

    if grant_type not in ("client_credentials","refresh_token"):
        print("unsupported grant_type")
        raise HTTPException(400)

    if grant_type == "client_credentials":
        if not body_dict.get("client_id") or not body_dict.get("client_secret"):
            print("invalid client credentials")
            raise HTTPException(400)
        owner = body_dict["client_id"]
        return JSONResponse(issue_tokens(owner))

    if grant_type == "refresh_token":
        r = body_dict.get("refresh_token")
        print(f"received token: {r}")
        return JSONResponse(issue_tokens("dummy owner"))

@app.get("/")
def root():
    return {"status": "ok"}
