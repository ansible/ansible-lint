# Used to generate JSON Validations chema for requirements.
import sys
from pathlib import Path
from typing import List, Optional, Union

if sys.version_info >= (3, 8):
    from typing import Literal  # pylint: disable=no-name-in-module
else:
    from typing_extensions import Literal

from pydantic import BaseModel, Extra, Field, HttpUrl


class PlatformModel(BaseModel):
    name: str
    versions: List[str]


class GalaxyInfoModel(BaseModel):
    role_name: Optional[str] = Field(regex=r"[a-z][a-z0-9_]+", min_length=2)
    author: Optional[str] = Field(regex=r"[a-z0-9][a-z0-9_]+", min_length=2)
    description: str
    company: str
    license: str
    min_ansible_version: str
    min_ansible_container_version: Optional[str]
    platforms: List[PlatformModel]
    galaxy_tags: List[str]

    class Config:
        extra = Extra.forbid


class DependencyModel(BaseModel):
    role: str
    src: Optional[str]
    # name: Union[str, HttpUrl] = Field(regex=r"[a-z][a-z0-9_]+\.[a-z0-9][a-z0-9_]+", min_length=2)
    # ^ url or galaxy namespace.rolename
    version: Optional[str]
    scm: Optional[Literal["hg", "git"]]

    class Config:
        extra = Extra.forbid


class MetaModel(BaseModel):
    galaxy_info: GalaxyInfoModel
    dependencies: List[DependencyModel]
    # https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html#using-allow-duplicates-true
    allow_duplicates: Optional[bool]

    class Config:
        extra = Extra.forbid
        title = 'Ansible Meta Schema'


# this is equivalent to json.dumps(MainModel.schema(), indent=2):
my_dir = Path(__file__).resolve().parents[1]
output_file = my_dir / "data" / "ansible-meta-schema.json"
with open(output_file, "w") as f:
    f.write(MetaModel.schema_json(indent=2))
    f.write("\n")
