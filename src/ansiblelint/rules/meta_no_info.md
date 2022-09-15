# meta-no-info

This rule checks role metadata for missing information.
Always set appropriate values for the following metadata fields in the `meta/main.yml` file, under `galaxy_info` key:

- `platforms`
- `min_ansible_version`

## Problematic Code

```yaml
---
# The metadata fields for minimum Ansible version and supported platforms are not set.
galaxy_info:
  min_ansible_version:
```

## Correct Code

```yaml
---
galaxy_info:
  min_ansible_version: "2.8"
  platforms:
    - name: Fedora
      versions:
        - all
```
