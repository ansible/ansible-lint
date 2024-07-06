# galaxy-version-incorrect

This rule checks that the `version` key within `galaxy.yml` is greater than or
equal to `1.0.0`. This is to follow semantic versioning standards that are
enforced in the Ansible Automation Platform.

This is an opt-in rule. You must enable it in your Ansible-lint configuration as
follows:

```yaml
enable_list:
  - galaxy-version-incorrect
```

## Problematic Code

```yaml
description: "description"
namespace: "namespace_name"
name: "collection_name"
version: "0.0.1" # <- version key is not greater than or equal to '1.0.0'.
readme: "README.md"
authors:
  - "Author1"
  - "Author2 (https://author2.example.com)"
  - "Author3 <author3@example.com>"
dependencies:
  "other_namespace.collection1": ">=1.0.0"
  "other_namespace.collection2": ">=2.0.0,<3.0.0"
  "anderson55.my_collection": "*" # note: "*" selects the highest version available
license:
  - "MIT"
tags:
  - demo
  - collection
repository: "https://www.github.com/my_org/my_collection"
```

## Correct Code

```yaml
description: "description"
namespace: "namespace_name"
name: "collection_name"
version: "1.0.0" # <- version key is greater than or equal to '1.0.0'.
readme: "README.md"
authors:
  - "Author1"
  - "Author2 (https://author2.example.com)"
  - "Author3 <author3@example.com>"
dependencies:
  "other_namespace.collection1": ">=1.0.0"
  "other_namespace.collection2": ">=2.0.0,<3.0.0"
  "anderson55.my_collection": "*" # note: "*" selects the highest version available
license:
  - "MIT"
tags:
  - demo
  - collection
repository: "https://www.github.com/my_org/my_collection"
```
