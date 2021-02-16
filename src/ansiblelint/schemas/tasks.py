# Used to generate JSON Validations Schema for requirements.
from typing import List, Union, Optional, Any, Mapping
from pathlib import Path

from pydantic import BaseModel, Extra, Field


class _SharedModel(BaseModel):
    # Properties shared between Play, Role, Block and Task
    any_errors_fatal: Optional[bool]
    become: Optional[bool]
    become_exe: Optional[str]
    become_flags: Optional[str]
    become_method: Optional[str]
    become_user: Optional[str]
    check_mode: Optional[bool]
    collections: Optional[List[str]]
    connection: Optional[str]
    debugger: Optional[str]
    diff: Optional[bool]
    environment: Optional[Mapping[str, str]]
    ignore_errors: Optional[bool]
    ignore_unreachable: Optional[bool]
    module_defaults: Optional[Any]
    name: Optional[str]  # SHOULD BE REQUIRED
    no_log: Optional[bool]
    port: Optional[int]
    remote_user: Optional[str]
    run_once: Optional[bool]
    tags: Optional[List[str]]
    throttle: Optional[int]
    timeout: Optional[int]
    vars: Optional[Mapping[str, Any]]
    when: Optional[Union[str, List[str]]]


class TaskModel(_SharedModel):
    action: str
    args: Optional[Mapping[str, Any]]
    async_: Optional[int] = Field(alias="async")
    changed_when: Optional[bool]
    delay: Optional[int]
    delegate_facts: Optional[str]
    delegate_to: Optional[str]
    failed_when: Optional[str]
    local_action: Optional[str]
    notify: Optional[str]
    poll: Optional[int]
    register_: Optional[str] = Field(alias="register")
    retries: Optional[int]
    until: Optional[str]
    loop: Optional[str]
    loop_control: Optional[Any]
    # depreacted looping:
    with_items: Optional[Union[str, List[str]]]
    with_dict: Optional[Any]
    with_fileglob: Optional[Any]
    with_filetree: Optional[Any]
    with_first_found: Optional[Any]
    with_together: Optional[Any]
    with_subelements: Optional[Any]
    with_sequence: Optional[Any]
    with_random_choice: Optional[Any]
    with_lines: Optional[Any]
    with_indexed_items: Optional[Any]
    with_ini: Optional[Any]
    with_flattened: Optional[Any]
    with_inventory_hostnames: Optional[Any]

    class Config:
        extra = Extra.forbid


class BlockModel(_SharedModel):
    always: "Optional[List[Union[TaskModel, BlockModel]]]" = None
    block: "Optional[List[Union[TaskModel, BlockModel]]]" = None
    rescue: "Optional[List[Union[TaskModel, BlockModel]]]" = None
    delegate_facts: Optional[str]
    delegate_to: Optional[str]


# https://pydantic-docs.helpmanual.io/usage/postponed_annotations/#self-referencing-models
BlockModel.update_forward_refs()


class TasksFileModel(BaseModel):
    __root__: List[Union[TaskModel, BlockModel]]


my_dir = Path(__file__).resolve().parents[1]
output_file = my_dir / "data" / "ansible-tasks-schema.json"
with open(output_file, "w") as f:
    f.write(TasksFileModel.schema_json(
        indent=2))
    f.write("\n")
    print(f"Dumped {output_file}")
