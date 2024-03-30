from pydantic import BaseModel


class BaseConfig(BaseModel):
    class Project(BaseModel):
        name: str = 'project'
        version: str = ''

    project: Project = Project()
    mode: str = 'production'

    @property
    def is_production(self):
        return self.mode.lower() == 'production'

    def dict(self, *args, **kwargs):
        config_dict = super().dict(*args, **kwargs)
        config_dict['is_production'] = self.is_production
        return config_dict
