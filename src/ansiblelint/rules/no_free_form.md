# no-free-form

This rule identifies any use of [free-form](https://docs.ansible.com/ansible/2.7/user_guide/playbooks_intro.html#action-shorthand)
module calling syntax and asks for switching to the full syntax.

**Free-form** syntax, also known as **inline** or **shorthand**, can produce
subtle bugs. It can also prevent editors and IDEs from providing feedback,
autocomplete and validation for the edited line.

```{note}
As long you just pass a YAML string that contains a `=` character inside as the
parameter to the action module name, we consider this as using free-formsyntax.
Be sure you pass a dictionary to the module, so the free-form parsing
is never triggered.
```

As `raw` module only accepts free-form, we trigger `no-free-form[raw]` only if
we detect the presence of `executable=` inside raw calls. We advice the
explicit use of `args:` dictionary for configuring the executable to be run.

## Problematic code

```yaml
---
- name: Example with discouraged free-form syntax
  hosts: localhost
  tasks:
    - name: Create a placefolder file
      ansible.builtin.command: chdir=/tmp touch foo # <-- don't use free-form
    - name: Use raw to echo
      ansible.builtin.raw: executable=/bin/bash echo foo # <-- don't use executable=
      changed_when: false
```

## Correct code

```yaml
---
- name: Example that avoids free-form syntax
  hosts: localhost
  tasks:
    - name: Create a placefolder file
      ansible.builtin.command:
        cmd: touch foo # <-- ansible will not touch it
        chdir: /tmp
    - name: Use raw to echo
      ansible.builtin.raw: echo foo
      args:
        executable: /bin/bash # <-- explicit is better
      changed_when: false
```
