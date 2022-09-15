# no-changed-when

This rule checks that tasks return changes to results or conditions.
Unless tasks only read information, you should ensure that they return changes in the following ways:

- Register results or conditions and use the `changed_when` clause.
- Use the `creates` or `removes` argument.

You should use the `when` clause to run tasks only if a check returns a particular result.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Does not handle any output or return codes
      ansible.builtin.command: cat {{ my_file | quote }} # <- Does not handle the command output.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Handle shell output with return code
      ansible.builtin.command: cat {{ my_file | quote }}
      register: my_output # <- Registers the command output.
      changed_when: my_output.rc != 0 # <- Uses the return code to define when the task has changed.
```
