# no-log-password

This rule ensures playbooks do not write passwords to logs when using loops.
Always set the `no_log: true` attribute to protect sensitive data.

While most ansible modules know to mark sensitive data, if you happen to use
secrets inside a loop, they could end up being logged in some cases. Adding
an explicit `no_log: true` should prevent accidental exposure.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Log user passwords
      ansible.builtin.user:
        name: john_doe
        comment: John Doe
        uid: 1040
        group: admin
        password: "{{ item }}"
      with_items:
        - wow
      no_log: false # <- Sets the no_log attribute to false.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Do not log user passwords
      ansible.builtin.user:
        name: john_doe
        comment: John Doe
        uid: 1040
        group: admin
        password: "{{ item }}"
      with_items:
        - wow
      no_log: true # <- Sets the no_log attribute to a non-false value.
```
