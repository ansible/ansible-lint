# syntax-check

Our linter runs `ansible-playbook --syntax-check` on all playbooks, and if any
of these reports a syntax error, this stops any further processing of these
files.

This error **cannot be disabled** due to being a prerequisite for other steps.
You can exclude these files from linting, but it is better to make sure they can
be loaded by Ansible. This is often achieved by editing the inventory file
and/or `ansible.cfg` so ansible can load required variables.

If undefined variables cause the failure, you can use the Jinja `default()`
filter to provide fallback values, like in the example below.

This rule is among the few `unskippable` rules that cannot be added to
`skip_list` or `warn_list`. One possible workaround is to add the entire file to
the `exclude_paths`. This is a valid approach for special cases, like testing
fixtures that are invalid on purpose.

One of the most common sources of errors is a failure to assert the presence of
various variables at the beginning of the playbook.

This rule can produce messages like:

- `syntax-check[empty-playbook]`: Empty playbook, nothing to do
- `syntax-check[malformed]`: A malformed block was encountered while loading a block
- `syntax-check[missing-file]`: Unable to retrieve file contents ... Could not find or access ...
- `syntax-check[unknown-module]`: couldn't resolve module/action
- `syntax-check[specific]`: for other errors not mentioned above.

## syntax-check[unknown-module]

The linter relies on ansible-core code to load the ansible code and it will
produce a syntax error if the code refers to ansible content that is not
installed. You must ensure that all collections and roles used inside your
repository are listed inside a [`requirements.yml`](https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#installing-roles-and-collections-from-the-same-requirements-yml-file) file, so the linter can
install them when they are missing.

Valid location for `requirements.yml` are:

- `requirements.yml`
- `roles/requirements.yml`
- `collections/requirements.yml`
- `tests/requirements.yml`
- `tests/integration/requirements.yml`
- `tests/unit/requirements.yml`

Note: If requirements are test related then they should be inside `tests/`.

## Problematic code

```yaml
---
- name:
    Bad use of variable inside hosts block (wrong assumption of it being
    defined)
  hosts: "{{ my_hosts }}"
  tasks: []
```

## Correct code

```yaml
---
- name: Good use of variable inside hosts, without assumptions
  hosts: "{{ my_hosts | default([]) }}"
  tasks: []
```
