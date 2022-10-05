# partial-become

This rule checks that privilege escalation is activated when changing users.

To perform an action as a different user with the ``become_user`` directive, you must set ``become: true``.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Start the httpd service as the apache user
      ansible.builtin.service:
        name: httpd
        state: started
        become_user: apache # <- Does not change the user because "become: true" is not set.
```

## Correct Code

```yaml
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Start the httpd service as the apache user
      ansible.builtin.service:
        name: httpd
        state: started
        become: true # <- Activates privilege escalation.
        become_user: apache # <- Changes the user with the desired privileges.
```