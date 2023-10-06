# command-instead-of-shell

This rule identifies uses of `shell` modules instead of a `command` one when
this is not really needed. Shell is considerably slower than command and should
be avoided unless there is a special need for using shell features, like
environment variable expansion or chaining multiple commands using pipes.

## Problematic Code

```yaml
---
- name: Problematic example
  hosts: localhost
  tasks:
    - name: Echo a message
      ansible.builtin.shell: echo hello # <-- command is better in this case
      changed_when: false
```

## Correct Code

```yaml
---
- name: Correct example
  hosts: localhost
  tasks:
    - name: Echo a message
      ansible.builtin.command: echo hello
      changed_when: false
```

!!! note

    This rule can be automatically fixed using [`--fix`](../autofix.md) option.
