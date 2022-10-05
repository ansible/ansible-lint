# only-builtins

This rule checks that playbooks use actions from the `ansible.builtin` collection only.

This is an opt-in rule.
You must enable it in your Ansible-lint configuration as follows:

```yaml
enable_list:
  - only-builtins
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Deploy a Helm chart for Prometheus
      kubernetes.core.helm: # <- Uses a non-builtin collection.
        name: test
        chart_ref: stable/prometheus
        release_namespace: monitoring
        create_namespace: true
```

## Correct Code

```yaml
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Run a shell command
      ansible.builtin.shell: echo This playbook uses actions from the builtin collection only.
```
