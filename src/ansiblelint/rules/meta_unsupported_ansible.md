# meta-unsupported-ansible

This rule checks the meta/runtime.yml `requires_ansible` key against the list of currently supported versions of ansible-core.

This rule can produce messages such:

- `requires_ansible` key must be set to a supported version.

Currently supported versions of ansible-core are:

- `2.9.10`
- `2.11.x`
- `2.12.x`
- `2.13.x`
- `2.14.x`

## Problematic code

```yaml
# runtime.yml
---
requires_ansible: ">=2.9"
```

## Correct code

```yaml
# runtime.yml
---
requires_ansible: ">=2.9.10"
```
