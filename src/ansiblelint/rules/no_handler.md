# no-handler

This rule checks for the correct handling of changes to results or conditions.

If a task has a `when: result.changed` condition, it effectively acts as a
[handler](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html#handlers).
The recommended approach is to use `notify` and move tasks to `handlers`.
If necessary you can silence the rule by add a `# noqa: no-handler` comment at the end of the line.

## Problematic Code

```yaml
---
- name: Example of no-handler rule
  hosts: localhost
  tasks:
    - name: Register result of a task
      ansible.builtin.copy:
        dest: "/tmp/placeholder"
        content: "Ansible made this!"
        mode: 0600
      register: result # <-- Registers the result of the task.
    - name: Second command to run
      ansible.builtin.debug:
        msg: The placeholder file was modified!
      when: result.changed # <-- Triggers the no-handler rule.
```

```yaml
---
# Optionally silences the rule.
when: result.changed # noqa: no-handler
```

## Correct Code

The following code includes the same functionality as the problematic code without recording a `result` variable.

```yaml
---
- name: Example of no-handler rule
  hosts: localhost
  tasks:
    - name: Register result of a task
      ansible.builtin.copy:
        dest: "/tmp/placeholder"
        content: "Ansible made this!"
        mode: 0600
      notify:
        - Second command to run # <-- Handler runs only when the file changes.
  handlers:
    - name: Second command to run
      ansible.builtin.debug:
        msg: The placeholder file was modified!
```
