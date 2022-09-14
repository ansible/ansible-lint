# fqcn-builtins

This rule checks that playbooks use the fully qualified collection name (FQCN) for modules in the `ansible.builtin` collection.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Shell
      shell: echo # <- This does not use the FQCN for the shell module.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Shell
      ansible.builtin.shell: echo # <- This uses the FQCN for the shell module.
```
