# meta-incorrect

This rule checks role metadata for fields with undefined or default values.
Always set appropriate values for the following metadata fields in the `meta/main.yml` file:

- `author`
- `description`
- `company`
- `license`

## Problematic Code

```yaml
---
# Metadata fields for the role contain default values.
galaxy_info:
  author: your name
  description: your role description
  company: your company (optional)
  license: license (GPL-2.0-or-later, MIT, etc)
```

## Correct Code

```yaml
---
galaxy_info:
  author: Leroy Jenkins
  description: This role will set you free.
  company: Red Hat
  license: Apache
```
