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

## Auto-fixing capability

### Before autofix

```yaml
---
- name: Fixture for deprecated-local-action
  hosts: localhost
  tasks:
    - name: Task example
      local_action:
        module: ansible.builtin.debug
```

### After autofix

```yaml
---
- name: Fixture for deprecated-local-action
  hosts: localhost
  tasks:
    - name: Task example
      ansible.builtin.debug:
      delegate_to: localhost
```
