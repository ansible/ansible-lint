# no-jinja-when

This rule checks conditional statements for Jinja expressions in curly brackets `{{ }}`.
Ansible processes conditionals statements that use the `when`, `failed_when`, and `changed_when` clauses as Jinja expressions.

An Ansible rule is to always use `{{ }}` except with `when` keys.
Using `{{ }}` in conditionals creates a nested expression, which is an Ansible
anti-pattern and does not produce expected results.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Shut down Debian systems
      ansible.builtin.command: /sbin/shutdown -t now
      when: "{{ ansible_facts['os_family'] == 'Debian' }}" # <- Nests a Jinja expression in a conditional statement.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Shut down Debian systems
      ansible.builtin.command: /sbin/shutdown -t now
      when: ansible_facts['os_family'] == "Debian" # <- Uses facts in a conditional statement.
```

!!! note

    This rule can be automatically fixed using [`--fix`](../autofix.md) option.
