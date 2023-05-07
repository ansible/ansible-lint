# Custom linting rules

Define and use your own sets of rules with Ansible-lint.

## Rule definitions

You define each custom rule in a unique Python class file. Default rules are
named _DeprecatedVariableRule.py_, etc.

Each rule should have a short description as a Python docstring wrapped in
triple quotes `"""` immediately after the class name. The short description
should be brief and meaningfully explain the purpose of the rule to users.

Each rule definition should have the following parts:

- `id` provides a unique identifier to the rule.
- `description` explains what the rule checks for.
- `tags` specifies one or more tags for including or excluding the rule.

### Match and matchtask methods

Each rule definition should also invoke one of the following methods:

- `match` takes a line and returns:
  - None or False if the line does not match the test.
  - True or a custom message if the line does match the test. (This allows one
    rule to test multiple behaviors - see e.g. the
    _CommandsInsteadOfModulesRule_.)
- `matchtask` operates on a single task or handler, such that tasks get
  standardized to always contain a _module_ key and _module_arguments_ key.
  Other common task modifiers, such as _when_, _with_items_, etc., are also
  available as keys if present in the task.

The following is an example rule that uses the `match` method:

```python
from ansiblelint.rules import AnsibleLintRule

class DeprecatedVariableRule(AnsibleLintRule):
    """Deprecated variable declarations."""

    id = 'EXAMPLE002'
    description = 'Check for lines that have old style ${var} ' + \
                  'declarations'
    tags = { 'deprecations' }

    def match(self, line: str) -> Union[bool, str]:
        return '${' in line
```

The following is an example rule that uses the `matchtask` method:

```python
from typing import TYPE_CHECKING, Any, Dict, Union

import ansiblelint.utils
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task

class TaskHasTag(AnsibleLintRule):
    """Tasks must have tag."""

    id = 'EXAMPLE001'
    description = 'Tasks must have tag'
    tags = ['productivity']

    def matchtask(self, task: Task, file: 'Lintable' | None = None) -> Union[bool,str]:
        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(task.keys()).isdisjoint(['include','fail']):
            return False

        # Task should have tags
        if not task.has_key('tags'):
              return True

        return False
```

The task argument to `matchtask` contains a number of keys - the critical one is
_action_. The value of `task['action']` contains the module being used, and the
arguments passed, both as key-value pairs and a list of other arguments (e.g.
the command used with shell).

## Packaging custom rules

Ansible-lint automatically loads and enables custom rules in Python packages
from the _custom_ subdirectory. This subdirectory is part of the Ansible-lint
installation directory, for example:

`/usr/lib/python3.8/site-packages/ansiblelint/rules/custom/`

To automatically load custom rules, do the following:

1. Package your custom rules as a Python package with a descriptive name.

2. Configure the \[options\] section of the `setup.cfg` of your custom rules
   Python package as in the following example:

   ```yaml
   [options]
   packages =
       ansiblelint.rules.custom.<your_custom_rules_subdir>
   package_dir =
       ansiblelint.rules.custom.<your_custom_rules_subdir> = <your_rules_source_code_subdir>
   ```

3. Install the Python package into
   `<ansible_lint_custom_rules_dir>/custom/<your_custom_rules_subdir>/`.
