# internal-error

This error can also be caused by internal bugs but also by custom rules.
Instead of just stopping tool execution, we generate the errors and continue
processing other files. This allows users to add this rule to their `warn_list`
until the root cause is fixed.

Keep in mind that once an `internal-error` is found on a specific file, no
other rules will be executed on that same file.

In almost all cases you will see more detailed information regarding the
original error or runtime exception that triggered this rule.

If these files are broken on purpose, like some test fixtures, you need to add
them to the `exclude_paths`.

## Problematic code

```yaml
---
- name: Some title {{ # <-- Ansible will not load this invalid jinja template
  hosts: localhost
  tasks: []
```

## Correct code

```yaml
---
- name: Some title
  hosts: localhost
  tasks: []
```

## ERROR! No hosts matched the subscripted pattern

If you see this error, it means that you tried to index a host group variable
that is using an index above its size.

Instead of doing something like `hosts: all[1]` which assumes that you have
at least two hosts in your current inventory, you better write something like
`hosts: "{{ all[1] | default([]) }}`, which is safe and do not produce runtime
errors. Use safe fallbacks to make your code more resilient.
