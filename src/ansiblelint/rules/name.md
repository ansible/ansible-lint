# name

This rule identifies several problems related to the naming of tasks and plays.
This is important because these names are the primary way to **identify** and
**document** executed operations on the console, logs or web interface.

This rule can produce messages as:

- `name[casing]` - All names should start with an uppercase letter for languages
  that support it.
- `name[missing]` - All tasks should be named.
- `name[play]` - All plays should be named.
- `name[prefix]` - Prefix task names in sub-tasks files. (opt-in)
- `name[template]` - Jinja templates should only be at the end of 'name'. This
  helps with the identification of tasks inside the source code when they fail.
  The use of templating inside `name` keys is discouraged as there are multiple
  cases where the rendering of the name template is not possible.

If you want to ignore some of the messages above, you can add any of them to the
`skip_list`.

## name[prefix]

This rule applies only to included task files that are not named `main.yml` or
are embedded within subdirectories. It suggests adding the stems of the file
path as a prefix to the task name.

For example, if you have a task named `Restart server` inside a file named
`tasks/deploy.yml`, this rule suggests renaming it to `deploy | Restart server`,
so it would be easier to identify where it comes from. If the file was named
`tasks/main.yml`, then the rule would have no effect.

For task files that are embedded within subdirectories, these subdirectories
will also be appended as part of the prefix. For example, if you have a task
named `Terminate server` inside a file named `tasks/foo/destroy.yml`, this rule
suggests renaming it to `foo | destroy | Terminate server`. If the file was
named `tasks/foo/main.yml` then the rule would recommend renaming the task to
`foo | main | Terminate server`.

For the moment, this sub-rule is just an **opt-in**, so you need to add it to
your `enable_list` to activate it.

!!! note

    This rule was designed by [Red Hat Community of Practice](https://redhat-cop.github.io/automation-good-practices/#_prefix_task_names_in_sub_tasks_files_of_roles). The reasoning behind it being
    that in a complex roles or playbooks with multiple (sub-)tasks file, it becomes
    difficult to understand which task belongs to which file. Adding a prefix, in
    combination with the role’s name automatically added by Ansible, makes it a
    lot easier to follow and troubleshoot a role play.

## Problematic code

```yaml
---
- hosts: localhost # <-- playbook name[play]
  tasks:
    - name: create placefolder file # <-- name[casing] due lack of capital letter
      ansible.builtin.command: touch /tmp/.placeholder
```

## Correct code

```yaml
---
- name: Play for creating placeholder
  hosts: localhost
  tasks:
    - name: Create placeholder file
      ansible.builtin.command: touch /tmp/.placeholder
```

!!! note

    `name[casing]` can be automatically fixed using [`--fix`](../autofix.md) option.
