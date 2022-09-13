# inline-env-var

This rule checks that playbooks do not set environment variables in the `ansible.builtin.command` module.

You should set environment variables with the `ansible.builtin.shell` module or the `environment` keyword.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Set environment variable
      ansible.builtin.command: MY_ENV_VAR=my_value # <- Sets an environment variable in the command module.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Set environment variable
      ansible.builtin.shell: echo $MY_ENV_VAR
      environment:
        MY_ENV_VAR: my_value # <- Sets an environment variable with the environment keyword.
```

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Set environment variable
      ansible.builtin.shell: MY_ENV_VAR=my_value # <- Sets an environment variable with the shell module.
```
