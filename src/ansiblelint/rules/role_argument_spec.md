# role-argument-spec

This rule checks that roles define an argument specification in one of the
following ways:

- A standalone file at `meta/argument_specs.yml` or `meta/argument_specs.yaml`.
- An `argument_specs` key embedded in `meta/main.yml` or `meta/main.yaml`.

Role argument specifications document expected variables, enable runtime
validation, and allow tools to generate documentation automatically.

For more details, see [Role argument validation](https://docs.ansible.com/projects/ansible/devel/user_guide/playbooks_reuse_roles.html#role-argument-validation).

This is an opt-in rule.
You must enable it in your Ansible-lint configuration as follows:

```yaml
enable_list:
  - role-argument-spec
```

## Skipping for a Specific Role

When the role has a `meta/main.yml` (or `meta/main.yaml`), the violation is
reported against that file. You can skip it by adding the file path to your
`.ansible-lint-ignore` file:

```text
# .ansible-lint-ignore
roles/my_role/meta/main.yml role-argument-spec skip
```

Or by adding a skip comment on the first line of `meta/main.yml` (or
`meta/main.yaml`):

```yaml
--- # noqa: role-argument-spec
dependencies: []
```

If the role has no meta file at all, the violation is reported against the
role directory itself. In that case, use the directory path in the ignore
file:

```text
# .ansible-lint-ignore
roles/my_role role-argument-spec skip
```

## Problematic Code

```yaml
# A role directory without meta/argument_specs.yml or .yaml,
# and no argument_specs key in meta/main.yml or .yaml
roles/
  my_role/
    tasks/
      main.yml
    meta/
      main.yml # no argument_specs key
```

## Correct Code

```yaml
# Option 1: Standalone file (meta/argument_specs.yml or .yaml)
roles/
  my_role/
    tasks/
      main.yml
    meta/
      main.yml
      argument_specs.yml # <-- role argument specification

# Option 2: Embedded in meta/main.yml (or .yaml)
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
