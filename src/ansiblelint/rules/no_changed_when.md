# no-changed-when

This rule checks that tasks return changes to results or conditions. Unless
tasks only read information, you should ensure that they return changes in the
following ways:

- Register results or conditions and use the `changed_when` clause.
- Use the `creates` or `removes` argument.

You should always use the `changed_when` clause on tasks that do not naturally
detect if a change has occurred or not. Some of the most common examples are
[shell] and [command] modules, which run arbitrary commands.

One very common workaround is to use a boolean value like `changed_when: false`
if the task never changes anything or `changed_when: true` if it always changes
something, but you can also use any expressions, including ones that use the
registered result of a task, like in our example below.

This rule also applies to handlers, not only to tasks because they are also
tasks.

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

[shell]:
  https://docs.ansible.com/ansible/latest/collections/ansible/builtin/shell_module.html
[command]:
  https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html
