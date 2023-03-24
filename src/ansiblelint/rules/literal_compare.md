# literal-compare

This rule checks for literal comparison with the `when` clause.
Literal comparison, like `when: var == True`, is unnecessarily complex.
Use `when: var` to keep your playbooks simple.

Similarly, a check like `when: var != True` or `when: var == False`
should be replaced with `when: not var`.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Print environment variable to stdout
      ansible.builtin.command: echo $MY_ENV_VAR
      when: ansible_os_family == True # <- Adds complexity to your playbook.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Print environment variable to stdout
      ansible.builtin.command: echo $MY_ENV_VAR
      when: ansible_os_family # <- Keeps your playbook simple.
```
