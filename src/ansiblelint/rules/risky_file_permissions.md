# risky-file-permissions

This rule is triggered by various modules that could end up creating new files
on disk with permissions that might be too open, or unpredictable. Please read
the documentation of each module carefully to understand the implications of
using different argument values, as these make the difference between using the
module safely or not. The fix depends on each module and also your particular
situation.

Some modules have a `create` argument that defaults to `true`. For those you
either need to set `create: false` or provide some permissions like `mode: 0600`
to make the behavior predictable and not dependent on the current system
settings.

Modules that are checked:

- [`ansible.builtin.assemble`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/assemble_module.html)
- [`ansible.builtin.copy`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html)
- [`ansible.builtin.file`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html)
- [`ansible.builtin.get_url`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/get_url_module.html)
- [`ansible.builtin.replace`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/replace_module.html)
- [`ansible.builtin.template`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html)
- [`community.general.archive`](https://docs.ansible.com/ansible/latest/collections/community/general/archive_module.html)
- [`community.general.ini_file`](https://docs.ansible.com/ansible/latest/collections/community/general/ini_file_module.html)

!!! warning

    This rule does not take [module_defaults](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_module_defaults.html) configuration into account.
    There are currently no plans to implement this feature because changing task location can also change task behavior.

## Problematic code

```yaml
---
- name: Unsafe example of using ini_file
  community.general.ini_file:
    path: foo
    create: true
```

## Correct code

```yaml
---
- name: Safe example of using ini_file (1st solution)
  community.general.ini_file:
    path: foo
    create: false  # prevents creating a file with potentially insecure permissions

- name: Safe example of using ini_file (2nd solution)
  community.general.ini_file:
    path: foo
    mode: "0600"  # explicitly sets the desired permissions, to make the results predictable

- name: Safe example of using copy (3rd solution)
  ansible.builtin.copy:
    src: foo
    dest: bar
    mode: preserve   # copy has a special mode that sets the same permissions as the source file
```
