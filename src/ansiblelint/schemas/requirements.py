# Used to generate JSON Validations chema for requirements.
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Extra, HttpUrl


class CollectionModel(BaseModel):
    name: Optional[str]
    source: Optional[Union[List[HttpUrl], HttpUrl]]

    class Config:
        extra = Extra.forbid


class RoleModel(BaseModel):
    name: str
    version: str

    class Config:
        extra = Extra.forbid


class RequiementsV2Model(BaseModel):
    collections: List[CollectionModel]
    roles: List[RoleModel]

    class Config:
        extra = Extra.forbid


class RequiremetnsFileModel(BaseModel):
    __root__: Union[List[RoleModel], RequiementsV2Model]


my_dir = Path(__file__).resolve().parents[1]
output_file = my_dir / "data" / "ansible-requirements-schema.json"
with open(output_file, "w") as f:
    f.write(RequiremetnsFileModel.schema_json(indent=2))
    f.write("\n")
