## syntax-check

Our linter does run `ansible-playbook --syntax-check` on all playbooks, and
if any of these reports a syntax error, this stops any further processing
of these files.

This error **cannot be disabled** due to being a prerequisite for other steps.
You can either exclude these files from linting or better assure they can be
loaded by Ansible. This is often achieved by editing the inventory file and/or
`ansible.cfg` so ansible can load required variables.

If undefined variables are the failure reason you could use the jinja
`default()` filter for providing fallback values, like in the example below.

This rule is among the few `unskippable` ones, rules that cannot be added
to `ignore_list` or `warn_list`. One possible workaround is to add the entire
file to the `exclude_list`. This is a valid approach for special cases, like
testing fixtures that are on-purpose invalid.

One of the most common sources of errors is failure to assert the presence of
various variables at the beginning of the playbook.

### Problematic code

```yaml
---
- name: Bad use of variable inside hosts block (wrong assumption of it being defined)
  hosts: "{{ my_hosts }}"
  tasks: []
```

### Correct code

```yaml
---
- name: Good use of variable inside hosts, without assumptions
  hosts: "{{ my_hosts | default([]) }}"
  tasks: []
```
