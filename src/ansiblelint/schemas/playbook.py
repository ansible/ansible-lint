# Used to generate JSON Validations chema for requirements.
import json
from pathlib import Path
from typing import Any, List, Mapping, Optional, Union, Literal

from pydantic import BaseModel, Extra, Field
from pydantic.schema import schema
from ansiblelint.schemas.tasks import TaskModel, _SharedModel


class RoleModel(_SharedModel):
    role: str
    delegate_to: Optional[str]
    vars: Optional[Mapping[str, Any]]
    tags: Optional[List[str]]


class PlayModel(_SharedModel):
    # based on https://docs.ansible.com/ansible/latest/reference_appendices/playbooks_keywords.html#play
    fact_path: Optional[str]
    force_handlers: Optional[bool]
    gather_facts: Optional[bool]
    gather_subset: Optional[bool]
    gather_timeout: Optional[int]
    handlers: Optional[List[TaskModel]]
    hosts: str  # REQUIRED
    max_fail_percentage: Optional[float]
    order: Optional[Literal["default", "sorted", "reverse_sorted", "reverse_inventory", "shuffle"]]
    post_tasks: Optional[List[TaskModel]]
    pre_tasks: Optional[List[TaskModel]]
    roles: Optional[List[Union[RoleModel, str]]]
    serial: Optional[int]
    strategy: Optional[str]
    tasks: Optional[List[TaskModel]]
    vars_files: Optional[List[str]]
    vars_prompt: Optional[List[str]]

    class Config:
        extra = Extra.forbid

class ImportPlaybookModel(BaseModel):
    import_playbook: str

    class Config:
        extra = Extra.forbid


class PlaybookFileModel(BaseModel):
    __root__: List[Union[PlayModel, ImportPlaybookModel]]


my_dir = Path(__file__).resolve().parents[1]
output_file = my_dir / "data" / "ansible-playbook-schema.json"
with open(output_file, "w") as f:
    # top_level_schema = schema(
    #     # [PlaybookModel, ImportPlaybookModel],
    #     PlaybookFileModel,
    #     title='Ansible Playbook Schema'
    # )
    # f.write(json.dumps(top_level_schema, indent=2))

    f.write(PlaybookFileModel.schema_json(
        indent=2))
    f.write("\n")
    print(f"Dumped {output_file}")
