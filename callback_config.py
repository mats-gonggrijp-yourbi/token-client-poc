from pydantic import BaseModel, field_validator
from ast import literal_eval
from typing import Any

class CallbackConfig(BaseModel):
    @field_validator('headers', mode='before')
    @classmethod
    def create_headers(cls, v: str) -> dict[str, str]:
        return literal_eval(v)
    
    @field_validator('refresh_token_keys', mode='before')
    @classmethod
    def create_refresh_token_keys(cls, v: str) -> list[Any]:
        return literal_eval(v)
    
    @field_validator('access_token_keys', mode='before')
    @classmethod
    def create_access_token_keys(cls, v: str) -> list[Any]:
        return literal_eval(v)
    
    id : int
    url : str
    headers : dict[str, str]
    body : str
    expires_in_seconds : int
    module_alias : str
    system_alias : str
    customer_alias : str
    instance_alias : str
    refresh_token_keys : list[Any]
    access_token_keys : list[Any]

    class Config:
        from_attributes = True 
