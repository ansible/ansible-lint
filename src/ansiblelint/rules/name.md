## name

This rule identifies several problems related to task naming. This is important
because these names are the primary way to identify executed tasks on console,
logs or web interface. Their role is also to document what a task is supposed
to do.

- `name[missing]` - All tasks are required to have a name
- `name[casing]` - All task names should start with a capital letter

### Problematic code

```yaml
---
- ansible.builtin.command: touch /tmp/.placeholder
```

### Correct code

```yaml
---
- name: Create placeholder file
  ansible.builtin.command: touch /tmp/.placeholder
```
