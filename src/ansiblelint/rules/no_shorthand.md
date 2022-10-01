# no-shorthand

This rule identifies any use of [short-hand (free-form)](https://docs.ansible.com/ansible/2.7/user_guide/playbooks_intro.html#action-shorthand)
module calling syntax and asks for switching to the full syntax.

**Shorthand** syntax, also known as **free-form**, is known to produce
subtle bugs. Short-hand syntax also prevents editors from providing feedback,
autocomplete and validation for the edited line.

```{note}
As long you just pass a YAML string that contains a `=` character inside as the
parameter to the action module name, we consider this as being shorthand
syntax. Be sure you pass a dictionary to the module, so the short-hand parsing
is never triggered.
```

## Problematic code

```yaml
---
- name: Example with discouraged shorthand syntax
  hosts: localhost
  tasks:
    - name: Create a placefolder file
      ansible.builtin.command: chdir=/tmp touch foo # <-- don't use shorthand
```

## Correct code

```yaml
---
- name: Example that avoids shorthand syntax
  hosts: localhost
  tasks:
    - name: Create a placefolder file
      ansible.builtin.command:
        cmd: touch foo # <-- ansible will not touch it
        chdir: /tmp
```
