from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import secrets, time
from typing import Any
from starlette.datastructures import FormData
import asyncio

app = FastAPI()
refresh_store: dict[str, dict[Any, Any]] = {}
timeout_check: dict[str, float] = {}

RESPONSE_TIME = 0.08

def parse_body(data: dict[Any, Any] | FormData) -> dict[Any, Any]:
    if isinstance(data, dict):
        return data
    return dict(data)

def issue_tokens(owner: str) -> dict[str, str | int]:
    access = secrets.token_hex(16)
    refresh = secrets.token_hex(32)
    refresh_store[refresh] = {"owner": owner, "issued_at": time.time(), "access_exp": time.time() + 30}
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "expires_in": 30}

@app.post("/token")
async def token(req: Request):
    # Mimick realistic server response times 
    await asyncio.sleep(RESPONSE_TIME) # 80ms

    body = await req.json() if req.headers.get("Content-Type","").startswith("application/json") else await req.form()
    body_dict: dict[Any, Any] = parse_body(body)
    grant_type = body_dict.get("grant_type")

    call_id: str | None = req.headers.get("id", None)
    if not call_id:
        raise HTTPException(500)

    curr_time = time.monotonic()
    exp_time = int(req.headers.get("expires_in_seconds", 0))

    if (last_time := timeout_check.get(call_id, None)):
        deadline = last_time + exp_time

        if curr_time > deadline:
            print((
                f"Callback for {call_id} was too late.\n"
                f"Deadline: {deadline} - Current time: {curr_time} "
                f"- Difference: {deadline - curr_time} seconds"
            ))
        else:
            print(f"Callback {call_id} within {deadline - curr_time} seconds of deadline")

    timeout_check[call_id] = curr_time


    if grant_type not in ("client_credentials","refresh_token"):
        raise HTTPException(400, "unsupported grant_type")

    if grant_type == "client_credentials":
        if not body_dict.get("client_id") or not body_dict.get("client_secret"):
            raise HTTPException(400,"invalid client credentials")
        owner = body_dict["client_id"]
        return JSONResponse(issue_tokens(owner))

    if grant_type == "refresh_token":
        r = body_dict.get("refresh_token")
        if r not in refresh_store:
            raise HTTPException(400,"invalid refresh_token")
        info = refresh_store.pop(r)
        # if time.time() > info["access_exp"]:
        #     print(f"refresh used after expiry by {info['owner']}")
        return JSONResponse(issue_tokens(info["owner"]))

@app.get("/")
def root():
    return {"status": "ok"}
