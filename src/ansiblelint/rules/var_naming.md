# var-naming

This rule checks variable names to ensure they conform with requirements.

Variable names must contain only lowercase alphanumeric characters and the underscore `_` character.
Variable names must also start with either an alphabetic or underscore `_` character.

For more information see the [creating valid variable names](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#creating-valid-variable-names) topic in Ansible documentation.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  vars:
    CamelCase: true # <- Contains a mix of lowercase and uppercase characters.
    ALL_CAPS: bar # <- Contains only uppercase characters.
    v@r!able: baz # <- Contains special characters.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  vars:
    lowercase: true # <- Contains only lowercase characters.
    no_caps: bar # <- Does not contains uppercase characters.
    variable: baz # <- Does not contain special characters.
```
