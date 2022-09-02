# galaxy collection version

This rule identifies if the collection version mentioned in galaxy.yml is ideal in terms of the version number being greater than or equal to 1.0.0.

This rule can produce messages such:

- `collection-version-missing[galaxy]` - galaxy.yaml should have version tag.
- `collection-version[galaxy]` - collection version should be greater than or equal to 1.0.0

If you want to ignore some of the messages above, you can add any of them to
the `ignore_list`.

## Problematic code

# galaxy.yml

```yaml
---
name: foo
namespace: bar
version: 0.2.3 # <-- collection version should be <= 1.0.0
authors:
  - John
readme: ../README.md
description: "..."
```

## Correct code

# galaxy.yml

```yaml
---
name: foo
namespace: bar
version: 1.0.0
authors:
  - John
readme: ../README.md
description: "..."
```
