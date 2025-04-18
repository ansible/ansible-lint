# meta-runtime

This rule checks the meta/runtime.yml `requires_ansible` key against the list of
currently supported versions of ansible-core.

This rule can produce messages such as:

- `meta-runtime[unsupported-version]` - `requires_ansible` key must refer to a
  currently supported version such as: >=2.15.0, >=2.16.0, >=2.17.0, >=2.18.0
- `meta-runtime[invalid-version]` - `requires_ansible` is not a valid
  requirement specification

Please note that the linter will allow only a full version of Ansible such
`2.16.0` and not allow their short form, like `2.16`. This is a safety measure
for asking authors to mention an explicit version that they tested with. Over
the years we spotted multiple problems caused by the use of the short versions,
users ended up trying an outdated version that was never tested against by the
collection maintainer.

## Problematic code

```yaml
# runtime.yml
---
requires_ansible: ">=2.9"
```

```yaml
# runtime.yml
---
requires_ansible: "2.17"
```

## Correct code

```yaml
# runtime.yml
---
requires_ansible: ">=2.17.0"
```

## Configuration

In addition to the internal list of supported Ansible versions, users can
configure additional values. This allows those that want to maintain content
that requires a version of ansible-core that is already out of support.

```yaml
# Also recognize these versions of Ansible as supported:
supported_ansible_also:
  - "2.14"
```
