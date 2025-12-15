from pydantic import BaseModel, field_validator
from ast import literal_eval


class CallbackConfig(BaseModel):
    @field_validator('headers', mode='before')
    @classmethod
    def str_to_dict(cls, v: str) -> dict[str, str]:
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
    refresh_token_keys : str
    access_token_keys : str

    class Config:
        from_attributes = True 
