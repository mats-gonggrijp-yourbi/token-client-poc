from typing import Optional
from pydantic import BaseModel, Field, field_validator
from ast import literal_eval

class AuthConfig(BaseModel):
    id: Optional[int] = Field(default=None)  
    url: str
    headers: dict[str, str]

    @field_validator('headers', mode="before")
    @classmethod
    def str_to_dict(cls, v: str) -> dict[str, str]:
        return literal_eval(v)

    body: str 
    expires_in: int
    module_alias: str 
    system_alias: str 
    customer_alias: str 
    instance_alias: str 

    class Config:
        from_attributes = True 
