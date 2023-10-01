# deprecated-local-action

This rule recommends using `delegate_to: localhost` instead of the
`local_action`.

## Problematic Code

```yaml
---
- name: Task example
  local_action: # <-- this is deprecated
    module: ansible.builtin.debug
```

## Correct Code

```yaml
- name: Task example
    ansible.builtin.debug:
  delegate_to: localhost # <-- recommended way to run on localhost
```

!!! note

    This rule can be automatically fixed using [`--fix`](../autofix.md) option.
