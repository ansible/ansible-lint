# loop-var-prefix

This rule avoids conflicts with nested looping tasks by enforcing an individual
variable name in loops. Ansible defaults to `item` as the loop variable. You can
use `loop_var` to rename it. Optionally require a prefix on the variable name.
The prefix can be configured via the `<loop_var_prefix>` setting.

This rule can produce the following messages:

- `loop-var-prefix[missing]` - Replace any unsafe implicit `item` loop variable
  by adding `loop_var: <variable_name>...`.
- `loop-var-prefix[wrong]` - Ensure the loop variable starts with
  `<loop_var_prefix>`.

This rule originates from the [Naming parameters section of Ansible Best
Practices guide][cop314].

## Settings

You can change the behavior of this rule by overriding its default regular
expression used to check loop variable naming. Keep in mind that the `{role}`
part is replaced with the inferred role name when applicable.

```yaml
# .ansible-lint
loop_var_prefix: "^(__|{role}_)"
```

This is an opt-in rule. You must enable it in your Ansible-lint configuration as
follows:

```yaml
enable_list:
  - loop-var-prefix
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Does not set a variable name for loop variables.
      ansible.builtin.debug:
        var: item # <- When in a nested loop, "item" is ambiguous
      loop:
        - foo
        - bar
    - name: Sets a variable name that doesn't start with <loop_var_prefix>.
      ansible.builtin.debug:
        var: zz_item
      loop:
        - foo
        - bar
      loop_control:
        loop_var: zz_item # <- zz is not the role name so the prefix is wrong
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Sets a unique variable_name with role as prefix for loop variables.
      ansible.builtin.debug:
        var: myrole_item
      loop:
        - foo
        - bar
      loop_control:
        loop_var: myrole_item # <- Unique variable name with role as prefix
```

[cop314]:
  https://redhat-cop.github.io/automation-good-practices/#_naming_parameters
