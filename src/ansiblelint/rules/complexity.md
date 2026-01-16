# complexity

This rule aims to warn about Ansible content that seems to be overly complex,
suggesting refactoring for better readability and maintainability.

## complexity[tasks]

`complexity[tasks]` will be triggered if the total number of tasks inside a file
is above 100. This counts all tasks across all plays, including tasks nested
within blocks. If encountered, you should consider using
[`ansible.builtin.include_tasks`](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/include_tasks_module.html)
to split your tasks into smaller files.

The threshold can be customized via the `max_tasks` configuration option
(default: 100).

## complexity[play]

`complexity[play]` will be triggered if the number of tasks at the play level
(not counting pre_tasks, post_tasks, or handlers) exceeds the configured limit.
This helps ensure that individual plays remain manageable.

## complexity[nesting]

`complexity[nesting]` will appear when a block contains too many nested levels,
by default that number is 20 but it can be changed inside the configuration file
by defining `max_block_depth` value.

    Replace nested block with an include_tasks to make code easier to maintain. Maximum block depth allowed is ...
