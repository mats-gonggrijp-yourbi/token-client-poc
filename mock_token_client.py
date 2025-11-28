from fastapi import FastAPI, Form, Header, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import time
import secrets

app = FastAPI(title="Mock OAuth2.0 Server")

security = HTTPBasic()

# ------------------------------------------------------------------------------
# Configuration: Provider-like variations
# ------------------------------------------------------------------------------
ENABLE_BASIC_AUTH = True  # Toggle Basic Auth requirement
EXPECTED_CLIENT_ID = "client123"
EXPECTED_CLIENT_SECRET = "secret123"

# These could come from a DB or memory. Here we keep it simple.
VALID_REFRESH_TOKENS: set[str] = set()

# ------------------------------------------------------------------------------
# Helper functions (OAuth2.0 core logic)
# ------------------------------------------------------------------------------

def generate_token(prefix: str) -> str:
    """Generate a simple unique token."""
    return f"{prefix}-{int(time.time())}-{secrets.token_hex(8)}"

def issue_token_pair() -> dict[str, str | int]:
    """Create a new access + refresh token pair."""
    access = generate_token("access")
    refresh = generate_token("refresh")
    VALID_REFRESH_TOKENS.add(refresh)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": 3600,
    }

def validate_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Optional provider-specific feature:
    Validate client_id + client_secret using HTTP Basic Auth.

    This is NOT required by OAuth2.0 core spec, but widely used by many providers.
    """
    if not ENABLE_BASIC_AUTH:
        return

    correct_id = secrets.compare_digest(credentials.username, EXPECTED_CLIENT_ID)
    correct_secret = secrets.compare_digest(credentials.password, EXPECTED_CLIENT_SECRET)

    if not (correct_id and correct_secret):
        raise HTTPException(status_code=401, detail="Invalid client credentials")

# ------------------------------------------------------------------------------
# Models (response objects)
# ------------------------------------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

# ------------------------------------------------------------------------------
# OAuth2.0 Token Endpoint
# ------------------------------------------------------------------------------
@app.post("/token", response_model=TokenResponse)
async def token(
    grant_type: str = Form(...),
    username: Optional[str] = Form(None),       # used for "password" grant
    password: Optional[str] = Form(None),       # used for "password" grant
    refresh_token: Optional[str] = Form(None),  # used for refresh flow
    client_id: Optional[str] = Form(None),      # optional depending on provider
    client_secret: Optional[str] = Form(None),  # optional depending on provider
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPBasicCredentials] = Depends(validate_basic_auth),
):
    """
    This endpoint mimics /token behavior found in OAuth2.0 providers.
    
    Supported grant types:
    - "password": simulate initial sign-in → access + refresh tokens
    - "refresh_token": simulate token refresh → new access + refresh tokens

    Provider-specific behaviors:
    - May require HTTP Basic Auth (enabled via ENABLE_BASIC_AUTH)
    - May require client_id/client_secret inside body instead of headers
    """

    # ------------------------------------------------------------------
    # 1. INITIAL USER SIGN-IN (grant_type=password)
    # ------------------------------------------------------------------
    if grant_type == "password":
        # -- Provider-specific behavior:
        # Some providers validate username/password here.
        # This mock simply checks if provided at all.
        if not username or not password:
            raise HTTPException(status_code=400, detail="Missing username or password")

        return issue_token_pair()

    # ------------------------------------------------------------------
    # 2. REFRESH TOKEN FLOW (grant_type=refresh_token)
    # ------------------------------------------------------------------
    if grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Missing refresh_token")
        if refresh_token not in VALID_REFRESH_TOKENS:
            raise HTTPException(status_code=400, detail="Invalid refresh_token")

        # Invalidate old refresh token (provider preference)
        VALID_REFRESH_TOKENS.discard(refresh_token)

        return issue_token_pair()

    # ------------------------------------------------------------------
    # Unsupported grant type
    # ------------------------------------------------------------------
    raise HTTPException(status_code=400, detail="Unsupported grant_type")
