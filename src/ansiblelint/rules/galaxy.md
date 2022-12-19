# galaxy

This rule identifies if the collection version mentioned in galaxy.yml is ideal in terms of the version number being greater than or equal to `1.0.0`.

This rule also looks for a changelog file in expected locations, detailed below in the Changelog Details section.

This rule can produce messages such:

- `galaxy[version-missing]` - `galaxy.yaml` should have version tag.
- `galaxy[version-incorrect]` - collection version should be greater than or equal to `1.0.0`
- `galaxy[no-changelog]` - collection is missing a changelog file in expected locations.

If you want to ignore some of the messages above, you can add any of them to
the `ignore_list`.

## Problematic code

```yaml
# galaxy.yml
---
name: foo
namespace: bar
version: 0.2.3 # <-- collection version should be >= 1.0.0
authors:
  - John
readme: ../README.md
description: "..."
```

## Correct code

```yaml
# galaxy.yml
---
name: foo
namespace: bar
version: 1.0.0
authors:
  - John
readme: ../README.md
description: "..."
```

# Changelog Details

This rule expects a `CHANGELOG.md` or `.rst` file in the collection root or a `changelogs/changelog.yaml` file.

If a `changelogs/changelog.yaml` file exists, the schema will be checked.

# Minimum required changelog.yaml file

```yaml
# changelog.yaml
---
releases: {}
