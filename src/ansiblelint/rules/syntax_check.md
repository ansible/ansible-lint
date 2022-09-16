# syntax-check

Our linter runs `ansible-playbook --syntax-check` on all playbooks, and
if any of these reports a syntax error, this stops any further processing
of these files.

This error **cannot be disabled** due to being a prerequisite for other steps.
You can exclude these files from linting, but it is better to make sure they can be
loaded by Ansible. This is often achieved by editing the inventory file and/or
`ansible.cfg` so ansible can load required variables.

If undefined variables cause the failure, you can use the jinja
`default()` filter to provide fallback values, like in the example below.

This rule is among the few `unskippable` rules that cannot be added to
`skip_list` or `warn_list`. One possible workaround is to add the entire file
to the `exclude_paths`. This is a valid approach for special cases, like testing
fixtures that are invalid on purpose.

One of the most common sources of errors is failure to assert the presence of
various variables at the beginning of the playbook.

## Problematic code

```yaml
---
- name: Bad use of variable inside hosts block (wrong assumption of it being defined)
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
