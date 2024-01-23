# jinja

This rule can report problems related to jinja2 string templates. The current
version can report:

- `jinja[spacing]` when there are no spaces between variables
  and operators, including filters, like `{{ var_name | filter }}`. This
  improves readability and makes it less likely to introduce typos.
- `jinja[invalid]` when the jinja2 template is invalid, like `{{ {{ '1' }} }}`,
  which would result in a runtime error if you try to use it with Ansible, even
  if it does pass the Ansible syntax check.

As jinja2 syntax is closely following Python one we aim to follow
[black](https://black.readthedocs.io/en/stable/) formatting rules. If you are
curious how black would reformat a small snippet feel free to visit
[online black formatter](https://black.vercel.app/) site. Keep in mind to not
include the entire jinja2 template, so instead of `{{ 1+2==3 }}`, do paste
only `1+2==3`.

In ansible, `changed_when`, `failed_when`, `until`, `when` are considered to
use implicit jinja2 templating, meaning that they do not require `{{ }}`. Our
rule will suggest the removal of the braces for these fields.

## Problematic code

```yaml
---
- name: Some task
  vars:
    foo: "{{some|dict2items}}" # <-- jinja[spacing]
    bar: "{{ & }}" # <-- jinja[invalid]
  when: "{{ foo | bool }}" # <-- jinja[spacing] - 'when' has implicit templating
```

## Correct code

```yaml
---
- name: Some task
  vars:
    foo: "{{ some | dict2items }}"
    bar: "{{ '&' }}"
  when: foo | bool
```

## Current limitations

In its current form, this rule presents the following limitations:

- Jinja2 blocks that have newlines in them will not be reformatted because we
  consider that the user deliberately wanted to format them in a particular way.
- Jinja2 blocks that use tilde as a binary operation are ignored because black
  does not support tilde as a binary operator. Example: `{{ a ~ b }}`.
- Jinja2 blocks that use dot notation with numbers are ignored because python
  and black do not allow it. Example: `{{ foo.0.bar }}`

!!! note

    This rule can be automatically fixed using [`--fix`](../autofix.md) option.
