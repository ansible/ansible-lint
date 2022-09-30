# command-instead-of-module

This rule will recommend you to use a specific ansible module instead for tasks
that are better served by a module, as these are more reliable, provide better
messaging and usually have additional features like the ability to retry.

In the unlikely case that the rule triggers false positives, you can disable it
by adding a comment like `# noqa: command-instead-of-module` to the same line.

You can check the [source](https://github.com/ansible/ansible-lint/blob/main/src/ansiblelint/rules/command_instead_of_module.py)
of the rule for all the known commands that trigger the rule and their allowed
list arguments of exceptions and raise a pull request to improve them.

## Problematic Code

```yaml
---
- name: Update apt cache
  hosts: all
  tasks:
    - name: Run apt-get update
      ansible.builtin.command: apt-get update # <-- better to use ansible.builtin.apt module
```

## Correct Code

```yaml
---
- name: Update apt cache
  hosts: all
  tasks:
    - name: Run apt-get update
      ansible.builtin.apt:
        update_cache: true
```
