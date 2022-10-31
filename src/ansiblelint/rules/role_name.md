# role-name

This rule checks role names to ensure they conform with requirements.

Role names must contain only lowercase alphanumeric characters and the underscore `_` character.
Role names must also start with an alphabetic character.

For more information see the [roles directory](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections_structure.html#roles-directory) topic in Ansible documentation.

`role-name[path]` message tells you to avoid using paths when importing roles.
You should only rely on Ansible's ability to find the role and refer to them
using fully qualified names.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  roles:
    - 1myrole # <- Does not start with an alphabetic character.
    - myrole2[*^ # <- Contains invalid special characters.
    - myRole_3 # <- Contains uppercase alphabetic characters.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  roles:
    - myrole1 # <- Starts with an alphabetic character.
    - myrole2 # <- Contains only alphanumeric characters.
    - myrole_3 # <- Contains only lowercase alphabetic characters.
```
