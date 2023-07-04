# galaxy

This rule identifies if the collection version mentioned in galaxy.yml is ideal
in terms of the version number being greater than or equal to `1.0.0`.

This rule looks for a changelog file in expected locations, detailed below in
the Changelog Details section.

This rule checks to see if the `galaxy.yml` file includes one of the required
tags for certification on Automation Hub. Additional custom tags can be added,
but one or more of these tags must be present for certification.

The tag list is as follows: `application`, `cloud`,`database`, `infrastructure`,
`linux`, `monitoring`, `networking`, `security`,`storage`, `tools`, `windows`.

This rule can produce messages such:

- `galaxy[version-missing]` - `galaxy.yaml` should have version tag.
- `galaxy[version-incorrect]` - collection version should be greater than or
  equal to `1.0.0`
- `galaxy[no-changelog]` - collection is missing a changelog file in expected
  locations.
- `galaxy[no-runtime]` - Please add a
  [meta/runtime.yml](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_structure.html#meta-directory-and-runtime-yml)
  file.
- `galaxy[tags]` - `galaxy.yaml` must have one of the required tags:
  `application`, `cloud`, `database`, `infrastructure`, `linux`, `monitoring`,
  `networking`, `security`, `storage`, `tools`, `windows`.
- `galaxy[invalid-dependency-version]` = Invalid collection metadata. Dependency
  version spec range is invalid

If you want to ignore some of the messages above, you can add any of them to the
`ignore_list`.

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

This rule expects a `CHANGELOG.md` or `.rst` file in the collection root or a
`changelogs/changelog.yaml` file.

If a `changelogs/changelog.yaml` file exists, the schema will be checked.

## Minimum required changelog.yaml file

```yaml
# changelog.yaml
---
releases: {}
```

# Required Tag Details

## Problematic code

```yaml
# galaxy.yml
---
namespace: bar
name: foo
version: 1.0.0
authors:
  - John
readme: ../README.md
description: "..."
license:
  - Apache-2.0
repository: https://github.com/ORG/REPO_NAME
```

## Correct code

```yaml
# galaxy.yml
---
namespace: bar
name: foo
version: 1.0.0
authors:
  - John
readme: ../README.md
description: "..."
license:
  - Apache-2.0
repository: https://github.com/ORG/REPO_NAME
tags: [networking, test_tag, test_tag_2]
```
