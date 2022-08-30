# deprecated-command-syntax

This rule identifies the use of shorthand (free-form) syntax as this is highly
discouraged inside playbooks, mainly because it can easily lead to bugs that
are hard to identify.

While using the free-form from the command line is ok, it should never be used
inside playbooks.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Perform chmod
      ansible.builtin.command: creates=B chmod 644 A # <-- do not use shorthand
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Perform chmod
      ansible.builtin.command: chmod 644 A
      args:
        creates: B
```
