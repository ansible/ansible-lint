# Custom Rules

## Creating Custom Rules

Rules are described using a class file per rule. Default rules are named
_DeprecatedVariableRule.py_, etc.

Each rule definition should have the following:

- ID: A unique identifier

- Short description: Brief description of the rule

- Description: What the rule is looking for

- Tags: One or more tags that may be used to include or exclude the rule

- At least one of the following methods:

  - `match` that takes a line and returns None or False, if the line doesn't
    match the test, and True or a custom message, when it does. (This allows
    one rule to test multiple behaviors - see e.g. the
    _CommandsInsteadOfModulesRule_.)
  - `matchtask` that operates on a single task or handler, such that tasks
    get standardized to always contain a _module_ key and _module_arguments_
    key. Other common task modifiers, such as _when_, _with_items_, etc., are
    also available as keys, if present in the task.

An example rule using `match` is:

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

An example rule using `matchtask` is:

```python
from typing import TYPE_CHECKING, Any, Dict, Union

import ansiblelint.utils
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable

class TaskHasTag(AnsibleLintRule):
    """Tasks must have tag."""

    id = 'EXAMPLE001'
    description = 'Tasks must have tag'
    tags = ['productivity']

    def matchtask(self, task: Dict[str, Any], file: 'Optional[Lintable]' = None) -> Union[bool,str]:
        # If the task include another task or make the playbook fail
        # Don't force to have a tag
        if not set(task.keys()).isdisjoint(['include','fail']):
            return False

        # Task should have tags
        if not task.has_key('tags'):
              return True

        return False
```

The task argument to `matchtask` contains a number of keys - the critical
one is _action_. The value of _task\['action'\]_ contains the module being used,
and the arguments passed, both as key-value pairs and a list of other arguments
(e.g. the command used with shell).

In ansible-lint 2.0.0, _task\['action'\]\['args'\]_ was renamed
_task\['action'\]\['module_arguments'\]_ to avoid a clash when a module actually
takes args as a parameter key (e.g. ec2_tag)

In ansible-lint 3.0.0 _task\['action'\]\['module'\]_ was renamed
_task\['action'\]\['\_\_ansible_module\_\_'\]_ to avoid a clash when a module take
module as an argument. As a precaution, _task\['action'\]\['module_arguments'\]_
was renamed _task\['action'\]\['\_\_ansible_arguments\_\_'\]_.

## Packaging Custom Rules

Ansible-lint provides a sub directory named _custom_ in its built-in rules,
`/usr/lib/python3.8/site-packages/ansiblelint/rules/custom/` for example, to
install custom rules since v4.3.1. The custom rules which are packaged as a
python package installed into this directory will be loaded and enabled
automatically by ansible-lint.

To make custom rules loaded automatically, you need the following:

- Packaging your custom rules as a python package named some descriptive ones
  like `ansible_lint_custom_rules_foo`.
- Make it installed into
  `<ansible_lint_custom_rules_dir>/custom/<your_custom_rules_subdir>/`.

You may accomplish the second by adding some configurations into the \[options\]
section of the `setup.cfg` of your custom rules python package like the
following.

```
[options]
packages =
    ansiblelint.rules.custom.<your_custom_rules_subdir>
package_dir =
    ansiblelint.rules.custom.<your_custom_rules_subdir> = <your_rules_source_code_subdir>
```
