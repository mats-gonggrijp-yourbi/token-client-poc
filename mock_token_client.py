from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import secrets, time
from typing import Any
from starlette.datastructures import FormData
import asyncio

app = FastAPI()
refresh_store: dict[str, dict[Any, Any]] = {}

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
    await asyncio.sleep(0.08) # 80ms

    body = await req.json() if req.headers.get("Content-Type","").startswith("application/json") else await req.form()
    body_dict: dict[Any, Any] = parse_body(body)
    grant_type = body_dict.get("grant_type")

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
        if time.time() > info["access_exp"]:
            print(f"refresh used after expiry by {info['owner']}")
        return JSONResponse(issue_tokens(info["owner"]))

@app.get("/")
def root():
    return {"status": "ok"}
