from pydantic import BaseModel, field_validator
from ast import literal_eval
from typing import Any

class CallbackConfig(BaseModel):
    @field_validator(
        'headers', 'refresh_token_keys', 'access_token_keys',
        mode='before'
    )
    @classmethod
    def parse_literal(cls, v: Any):
        if isinstance(v, str):
            return literal_eval(v)
        return v

    id: int
    url: str
    headers: dict[str, str]
    body: str
    expires_in_seconds: int
    module_alias: str
    system_alias: str
    customer_alias: str
    instance_alias: str
    refresh_token_keys: list[Any]
    access_token_keys: list[Any]

    class Config:
        from_attributes = True
