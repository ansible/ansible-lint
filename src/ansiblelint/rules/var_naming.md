# var-naming

This rule checks variable names to ensure they conform with requirements.

Variable names must contain only lowercase alphanumeric characters and the
underscore `_` character. Variable names must also start with either an
alphabetic or underscore `_` character.

For more information see the [creating valid variable names][var-names] topic in
Ansible documentation and [Naming things (Good Practices for Ansible)][cop].

You should also be fully aware of [special variables][magic-vars], also known as
magic variables, especially as most of them can only be read. While Ansible will
just ignore any attempt to set them, the linter will notify the user, so they
would not be confused about a line that does not effectively do anything.

Possible errors messages:

- `var-naming[non-string]`: Variables names must be strings.
- `var-naming[non-ascii]`: Variables names must be ASCII.
- `var-naming[no-keyword]`: Variables names must not be Python keywords.
- `var-naming[no-jinja]`: Variables names must not contain jinja2 templating.
- `var-naming[pattern]`: Variables names should match ... regex.
- `var-naming[no-role-prefix]`: Variables names from within roles should use
  `role_name_` as a prefix. Underlines are accepted before the prefix.
- `var-naming[no-reserved]`: Variables names must not be Ansible reserved names.
- `var-naming[read-only]`: This special variable is read-only.

!!! note

    When using `include_role` or `import_role` with `vars`, vars should start
    with included role name prefix. As this role might not be compliant
    with this rule yet, you might need to temporarily disable this rule using
    a `# noqa: var-naming[no-role-prefix]` comment.

## Settings

This rule behavior can be changed by altering the below settings:

```yaml
# .ansible-lint
var_naming_pattern: "^[a-z_][a-z0-9_]*$"
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  vars:
    CamelCase: true # <- Contains a mix of lowercase and uppercase characters.
    ALL_CAPS: bar # <- Contains only uppercase characters.
    v@r!able: baz # <- Contains special characters.
    hosts: [] # <- hosts is an Ansible reserved name
    role_name: boo # <-- invalid as being Ansible special magic variable
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
    my_hosts: [] # <- Does not use a reserved names.
    my_role_name: boo
```

[cop]: https://redhat-cop.github.io/automation-good-practices/#_naming_things
[var-names]:
  https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#creating-valid-variable-names
[magic-vars]:
  https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html
