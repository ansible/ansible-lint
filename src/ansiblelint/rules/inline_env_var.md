# inline-env-var

This rule checks that playbooks do not set environment variables in the `ansible.builtin.command` module.

You should use the `environment` keyword to set environment variables.
Using `environment` keeps tasks compatible with `ansible.builtin.command` and
avoids conflicting with the `command-instead-of-shell` rule.

Use `ansible.builtin.shell` only when the task needs shell features, such as
variable expansion, pipes, or redirects.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Set environment variable
      ansible.builtin.command: MY_ENV_VAR=my_value printenv MY_ENV_VAR # <- Sets an environment variable in the command module.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Set environment variable
      ansible.builtin.command: printenv MY_ENV_VAR
      environment:
        MY_ENV_VAR: my_value # <- Sets an environment variable with the environment keyword.
```

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Expand environment variable with shell
      ansible.builtin.shell: echo $MY_ENV_VAR # <- Uses shell for variable expansion.
      environment:
        MY_ENV_VAR: my_value
```
