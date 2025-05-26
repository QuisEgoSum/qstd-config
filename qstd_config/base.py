from pydantic import BaseModel


class BaseConfig(BaseModel):
    class Project(BaseModel):
        name: str
        version: str

    @property
    def is_ready(self) -> bool:
        raise NotImplementedError  # real signature in ProxyConfig
