## name

This rule identifies several problems related to naming of tasks and plays.
This is important because these names are the primary way to identify executed
operations on console, logs or web interface. Their role is also to document
what Ansible is supposed to do.

This rule can produce messages such:

- `name[casing]` - All names should start with an uppercase letter.
- `name[missing]` - All tasks should be named.
- `name[play]` - All plays should be named.

### Problematic code

```yaml
---
- hosts: localhost
  tasks:
    - ansible.builtin.command: touch /tmp/.placeholder
```

### Correct code

```yaml
---
- name: Play for creating playholder
  hosts: localhost
  tasks:
    - name: Create placeholder file
      ansible.builtin.command: touch /tmp/.placeholder
```
