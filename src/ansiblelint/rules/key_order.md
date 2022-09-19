# key-order

This rule recommends reordering key names in ansible content to make
code easier to maintain and less prone to errors.

Here are some examples of common ordering checks done for tasks and handlers:

- `name` must always be the first key for plays, tasks and handlers
- on tasks, the `block`, `rescue` and `always` keys must be the last keys,
  as this would avoid accidental miss-indentation errors between the last task
  and the parent level.

## Problematic code

```yaml
---
- hosts: localhost
  name: This is a playbook # <-- name key should be the first one
  tasks: []
```

## Correct code

```yaml
---
- name: This is a playbook
  hosts: localhost
  tasks: []
```
