# no-handler

If a task has a `when: result.changed` condition, it is effectively acting as a
[handler](https://docs.ansible.com/ansible/latest/user_guide/playbooks_handlers.html).
You could use `notify` and move that task to `handlers`.
This rule checks for the correct handling of changes to results or conditions.

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
      register: result # <-- we register the result of the task

    - name: Second command to run
      ansible.builtin.debug:
        msg: The placeholder file was modified!
      when: result.changed # <-- this triggers no-handler rule
```

## Correct Code

Below you can see the corrected code, which has the same functionality while
avoiding recording a `result` variable. For simple cases, this approach is to
be preferred but you can always silence the rule by adding a
`# noqa: no-handler` comment at the end of the line.

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
        - Second command to run # <-- handler will run only when file is changed
  handlers:
    - name: Second command to run
      ansible.builtin.debug:
        msg: The placeholder file was modified!
```
