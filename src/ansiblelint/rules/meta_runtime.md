# meta-runtime

This rule checks the meta/runtime.yml `requires_ansible` key against the list of currently supported versions of ansible-core.

This rule can produce messages such as:

- `meta-runtime[unsupported-version]` - `requires_ansible` key must refer to a currently supported version such as: >=2.14.0, >=2.15.0, >=2.16.0
- `meta-runtime[invalid-version]` - `requires_ansible` is not a valid requirement specification

Please note that the linter will allow only a full version of Ansible such `2.16.0` and not allow their short form, like `2.16`. This is a safety measure
for asking authors to mention an explicit version that they tested with. Over the years we spotted multiple problems caused by the use of the short versions, users
ended up trying an outdated version that was never tested against by the collection maintainer.

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
