# complexity

This rule aims to warn about Ansible content that seems to be overly complex,
suggesting refactoring for better readability and maintainability.

`complexity[tasks]` will be triggered if the total number of tasks inside a file
is above 100. If encountered, you are should consider using
[`ansible.builtin.include_tasks`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/include_tasks_module.html)
to split your tasks into smaller files.
