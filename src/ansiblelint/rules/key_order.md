# key-order

This rule recommends reordering key names in ansible content in order to make
code easier to maintain and avoid mistakes.

Here are some examples of common ordering checks done:

- `name` must always be the first key for plays, tasks and handlers
- when present, the `block` key must be the last, avoid accidental indentation
  bugs moving keys between block and the last task within the block.

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
