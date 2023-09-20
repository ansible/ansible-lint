# meta-runtime

This rule checks the meta/runtime.yml `requires_ansible` key against the list of currently supported versions of ansible-core.

This rule can produce messages such:

- `requires_ansible` key must be set to a supported version.

Currently supported versions of ansible-core are:

- `2.13.x`
- `2.14.x`
- `2.15.x`

This rule can produce messages such as:

- `meta-runtime[unsupported-version]` - `requires_ansible` key must contain a supported version - 2.13.x, 2.14.x, 2.15.x.
- `meta-runtime[invalid-version]` - `requires_ansible` is not a valid requirement specification


## Problematic code

```yaml
# runtime.yml
---
requires_ansible: ">=2.9"
```


```yaml
# runtime.yml
---
requires_ansible: "2.14"
```

## Correct code

```yaml
# runtime.yml
---
requires_ansible: ">=2.14.0"
```
