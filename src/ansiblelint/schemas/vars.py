# Used to generate JSON Validations chema for requirements.
from pathlib import Path
from typing import Dict, Any, Generator, Tuple

from pydantic import BaseModel


class VarsModel(BaseModel):
    # __root__: Dict[str, Any] = {"foo": "bar"}

    # def __iter__(self) -> Any:
    #     return iter(self.__root__)

    # def __getattr__(self, item: str) -> Any:
    #     return self.__root__[item]

    class Config:
        title = 'Ansible Vars Schema'


# this is equivalent to json.dumps(VarsModel.schema(), indent=2):
my_dir = Path(__file__).resolve().parents[1]
output_file = my_dir / "data" / "ansible-vars-schema.json"
with open(output_file, "w") as f:
    f.write(VarsModel.schema_json(indent=2))
    f.write("\n")
