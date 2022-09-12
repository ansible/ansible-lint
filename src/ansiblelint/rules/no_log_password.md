# no-log-password

This rule ensures playbooks do not write passwords to logs.
Always set the `no_log: True` attribute to protect sensitive data.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Log user passwords
      ansible.builtin.user:
        name: johnd
        comment: John Doe
        uid: 1040
        group: admin
        password: password
      no_log: False # <- Sets the no_log attribute to false.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Do not log user passwords
      ansible.builtin.user:
        name: johnd
        comment: John Doe
        uid: 1040
        group: admin
        password: password
      no_log: True # <- Sets the no_log attribute to a non-false value.
```
