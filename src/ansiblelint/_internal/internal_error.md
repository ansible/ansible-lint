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
them to the `exclude_list`.

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
