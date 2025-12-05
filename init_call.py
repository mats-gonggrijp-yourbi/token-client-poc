import httpx
import json
from callback_config import CallbackConfig
from scheduled_callback import ScheduledCallback
from urllib.parse import parse_qsl, urlencode


async def update_client_credentials(
        body: dict[str, str],
        sb: ScheduledCallback
    ):
    # Add client ID and secret if they are necessary
    if "client_id" in body:
        client_id = await sb.secret_client.get_secret("ClientId")
        if client_id:
            body["client_id"] = client_id
        else:
            raise ValueError("Missing client id in keyvault")

    if "client_secret" in body:
        client_secret = await sb.secret_client.get_secret("ClientId")
        if client_secret:
            body["client_secret"]
        else:
            raise ValueError("Missing client secret keyvault")


async def initial_call(
        sc: ScheduledCallback, c: CallbackConfig, url: str, client_id: str
    ):

    headers = {"Content-Type": "application/json"}
    body = f'''
    {{
        "grant_type": "client_credentials",
        "client_id": "{client_id}",
        "client_secret": "test"
    }}
    '''
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=url,
            headers=headers,
            content=body
        )
    data = response.json()
    rt = data["refresh_token"]
    at = data["access_token"]
    ctype = c.headers["Content-Type"]
    if ctype == "application/x-www-form-urlencoded":
        body = dict(parse_qsl(c.body))
        await update_client_credentials(body, sc)
        body['refresh_token'] = rt
        c.body = urlencode(body)

    elif ctype == "application/json":
        body = json.loads(c.body)
        await update_client_credentials(body, sc)
        body['refresh_token'] = rt
        c.body = json.dumps(body)

    # Set the refresh and access tokens in the customer's keyvault
    await sc.secret_client.set_secret("RefreshToken", rt)
    await sc.secret_client.set_secret("AccessToken", at)

    return None