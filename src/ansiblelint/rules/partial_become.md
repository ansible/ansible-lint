# partial-become

This rule checks that privilege escalation is activated when changing users.

To perform an action as a different user with the `become_user` directive, you must set `become: true`.

```{warning}
While Ansible inherits have of `become` and `become_user` from upper levels,
like play level or command line, we do not look at these values. This rule
requires you to be explicit and always define both in the same place, mainly
in order to prevent accidents when some tasks are moved from one location to
another one.
```

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
