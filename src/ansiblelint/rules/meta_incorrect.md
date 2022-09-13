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
  description: Lorem ipsum dolor sit amet.
  company: Red Hat
  license: |
    This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
    To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/
    or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
```
