from pydantic import BaseModel, field_validator
from ast import literal_eval


class CallbackConfig(BaseModel):
    @field_validator('headers', mode='before')
    @classmethod
    def str_to_dict(cls, v: str) -> dict[str, str]:
        return literal_eval(v)
    
    scale : str
    seconds_per_tick : int
    id : int
    url : str
    headers : dict[str, str]
    body : str
    expires_in_seconds : int
    time_wheel_scale : str
    module_alias : str
    system_alias : str
    customer_alias : str
    instance_alias : str
    expires_in_ticks: int
    wait_time_in_ticks: int

    class Config:
        from_attributes = True 
