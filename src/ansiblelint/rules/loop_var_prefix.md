# loop-var-prefix

This rule avoids conflicts with nested looping tasks by configuring a variable prefix with `loop_var`.
Ansible sets `item` as the loop variable.
You can use `loop_var` to specify a prefix for loop variables and ensure they are unique to each task.

This rule can produce the following messages:

- `[loop-var-prefix[missing]` - Replace unsafe implicit `item` loop variable by adding `loop_var: <loop_var_prefix>...`.
- `[loop-var-prefix[wrong]` - Loop variable should start with <loop_var_prefix>

This is an opt-in rule.
You must enable it in your Ansible-lint configuration as follows:

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
    - name: Does not set a prefix for loop variables.
      ansible.builtin.debug:
        var: item
      loop:
        - foo
        - bar # <- These items do not have a unique prefix.
    - name: Sets
      ansible.builtin.debug:
        var: zz_item
      loop:
        - foo
        - bar
      loop_control:
        loop_var: zz_item # <- This prefix is not unique.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Sets a unique prefix for loop variables.
      ansible.builtin.debug:
        var: zz_item
      loop:
        - foo
        - bar
      loop_control:
        loop_var: my_prefix # <- Specifies a unique prefix for loop variables.
```
