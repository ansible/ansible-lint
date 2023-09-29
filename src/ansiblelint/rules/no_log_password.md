# no-log-password

This rule ensures playbooks do not write passwords to logs when using loops.
Always set the `no_log: true` attribute to protect sensitive data.

While most Ansible modules mask sensitive data, using secrets inside a loop can result in those secrets being logged.
Explicitly adding `no_log: true` prevents accidentally exposing secrets.

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

!!! note

    This rule can be automatically fixed using [`--fix`](../autofix.md) option.
