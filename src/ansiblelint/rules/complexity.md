# complexity

This rule aims to warn about Ansible content that seems to be overly complex,
suggesting refactoring for better readability and maintainability.

## complexity[tasks]

`complexity[tasks]` will be triggered if the total number of tasks inside a file
is above 100. If encountered, you should consider using
[`ansible.builtin.include_tasks`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/include_tasks_module.html)
to split your tasks into smaller files.

## complexity[nesting]

`complexity[nesting]` will appear when a block contains too many tasks, by
default that number is 20 but it can be changed inside the configuration file by
defining `max_block_depth` value.

    Replace nested block with an include_tasks to make code easier to maintain. Maximum block depth allowed is ...
