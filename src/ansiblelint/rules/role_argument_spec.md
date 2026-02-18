# role-argument-spec

This rule checks that roles define an argument specification file at
`meta/argument_specs.yml` (or `meta/argument_specs.yaml`). Alternatively,
`argument_specs` can be embedded in `meta/main.yml`.

Role argument specifications document expected variables, enable runtime
validation, and allow tools to generate documentation automatically.

For more details, see [Role argument validation](https://docs.ansible.com/projects/ansible/devel/user_guide/playbooks_reuse_roles.html#role-argument-validation).

This is an opt-in rule. You must enable it by adding `role-argument-spec` to your
`enable_list` configuration.

## Problematic Code

```yaml
# A role directory without meta/argument_specs.yml
roles/
  my_role/
    tasks/
      main.yml
    meta/
      main.yml # no argument_specs key
```

## Correct Code

```yaml
# Option 1: Standalone argument_specs.yml
roles/
  my_role/
    tasks/
      main.yml
    meta/
      main.yml
      argument_specs.yml # <-- role argument specification

# Option 2: Embedded in meta/main.yml
# meta/main.yml
---
dependencies: []
argument_specs:
  main:
    short_description: The main entry point for the role.
    options:
      my_var:
        type: str
        required: true
        description: An example variable.
```
