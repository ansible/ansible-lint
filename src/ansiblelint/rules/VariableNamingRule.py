from typing import TYPE_CHECKING, List, Any, Dict, Union

from ansiblelint.config import options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import toidentifier
from ansiblelint.utils import parse_yaml_from_file
import ansible.parsing.yaml.objects

# if TYPE_CHECKING:
#     from typing import Any, Dict, Union
#     from ansiblelint.constants import odict

import re # used for regex string validation
import json

# ---------------------------------------------------------------
# TODO: Check task for registered variables
# TODO: Check task for set_facts
# TODO: Check vars files
# TODO: Ensure variable names do not match one of the magic variable names
#       https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html#special-variables
# TODO: Provide comment on following open issue:
#       [Ansible-lint does not catch invalid variable names](https://github.com/ansible/ansible-lint/issues/447)
# ---------------------------------------------------------------

# properties/parameters are prefixed and postfixed with `__`
def is_property(k):
    return (k.startswith('__') and k.endswith('__'))

def is_invalid_variable_name(text):
    patterns = '^[a-z0-9_]*$'
    if re.search(patterns, text):
      return False # string uses acceptable characters
    else:
      return True # string uses unacceptable characters

class VariableNamingRule(AnsibleLintRule):
    id = 'var-naming'
    base_msg = 'All variables should be named using only lowercase and underscores'
    shortdesc = base_msg
    description = 'All variables should be named using only lowercase and underscores'
    severity = 'MEDIUM' # ansible-lint displays severity when with --parseable-severity option
    tags = ['formatting', 'readability']
    version_added = 'v5.0.5'

    def recursive_items(self, dictionary):
        """Return a recursive search for all keys in the dictionary """

        for key, value in dictionary.items():
            # Avoid internal properties in the dictionary
            if not is_property(key):
                # Recurse if value is another ansible dictionary
                if isinstance(value, ansible.parsing.yaml.objects.AnsibleMapping):
                    yield (key, value)
                    yield from self.recursive_items(value)
                else:
                    yield (key, value)

    def matchplay(self, file: "Lintable", data: "odict[str, Any]") -> List["MatchError"]:
        """Return matches found for a specific playbook."""
        results = []

        # If the Play uses the 'vars' section to set variables
        vars = data.get('vars', {})
        for key, value in self.recursive_items(vars):
            if is_invalid_variable_name(key):
                results.append(
                    self.create_matcherror(
                          filename=file, 
                          linenumber=vars['__line__'], 
                          message="Play defines variable '" + key + "' within 'vars' section that violates variable naming standards"
                    )
                )

        return results

    def matchtask(self, task: Dict[str, Any]) -> Union[bool, str]:
        """Return matches for task based variables."""

        results: List["MatchError"] = []

        # If the task uses the 'vars' section to set variables
        vars = task.get('vars', {})
        for key, value in self.recursive_items(vars):
            if is_invalid_variable_name(key):
                return "Task defines variables within 'vars' section that violates variable naming standards"

        # If the task uses the 'set_fact' module
        ansible_module = task['action']['__ansible_module__']
        ansible_action = task['action']
        if ansible_module == 'set_fact':
            for key, value in self.recursive_items(ansible_action):
                if is_invalid_variable_name(key):
                    return "Task uses 'set_fact' to define variables that violates variable naming standards"

        # If the task registers a variable
        registered_var = task.get('register', None)
        if registered_var and is_invalid_variable_name(registered_var):
            return "Task registers a variable that violates variable naming standards"

        return False

    def matchyaml(self, file: Lintable) -> List["MatchError"]:
        """Return matches for variables defined in vars files."""

        results: List["MatchError"] = []
        meta_data = {}

        if file.kind == "vars":
            meta_data = parse_yaml_from_file(str(file.path))
            for key, value in self.recursive_items(meta_data):
                if is_invalid_variable_name(key):
                    results.append(
                        self.create_matcherror(
                              filename=file, 
                              #linenumber=vars['__line__'], 
                              message="File defines variable '" + key + "' that violates variable naming standards"
                        )
                    )
        else:
            results.extend(super().matchyaml(file))
        return results