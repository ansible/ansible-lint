# deprecated-local-action

This rule recommends using `delegate_to: localhost` instead of the
`local_action`.

## Problematic Code

```yaml
---
- name: Task example
  local_action: # <-- this is deprecated
    module: boto3_facts
```

## Correct Code

```yaml
- name: Task example
    boto3_facts:
  delegate_to: localhost # <-- recommended way to run on localhost
```
