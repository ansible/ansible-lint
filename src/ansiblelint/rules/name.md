# name

This rule identifies several problems related to the naming of tasks and plays.
This is important because these names are the primary way to **identify** and
**document** executed operations on console, logs or web interface.

This rule can produce messages such:

- `name[casing]` - All names should start with an uppercase letter for
  languages that support it.
- `name[missing]` - All tasks should be named.
- `name[play]` - All plays should be named.
- `name[template]` - Jinja templates should only be at the end of 'name'. This
  helps with the identification of tasks inside the source code when they fail.
  The use of templating inside `name` keys is discouraged as there
  are multiple cases where the rendering of the name template is not possible.

If you want to ignore some of the messages above, you can add any of them to
the `skip_list`.

## Problematic code

```yaml
---
- hosts: localhost # <-- playbook missing a name key
  tasks:
    - name: create placefolder file # <-- not starting with a capital letter
      ansible.builtin.command: touch /tmp/.placeholder
```

## Correct code

```yaml
---
- name: Play for creating playholder
  hosts: localhost
  tasks:
    - name: Create placeholder file
      ansible.builtin.command: touch /tmp/.placeholder
```
