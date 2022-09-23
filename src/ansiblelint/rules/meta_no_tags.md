# meta-no-tags

This rule checks role metadata for tags with special characters.
Always use lowercase numbers and letters for tags in the `meta/main.yml` file.

## Problematic Code

```yaml
---
# Metadata tags contain upper-case letters and special characters.
galaxy_info:
  galaxy_tags: [MyTag#1, MyTag&^-]
```

## Correct Code

```yaml
---
# Metadata tags contain only lowercase letters and numbers.
galaxy_info:
  galaxy_tags: [mytag1, mytag2]
```
