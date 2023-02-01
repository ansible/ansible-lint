# no-relative-paths

This rule checks for relative paths in the `ansible.builtin.copy` and
`ansible.builtin.template` modules.

Relative paths in a task most often direct Ansible to remote files and
directories on managed nodes. In the `ansible.builtin.copy` and
`ansible.builtin.template` modules, the `src` argument refers to local files and
directories on the control node.

The recommended locations to store files are as follows:

- Use the `files/` folder in the playbook or role directory for the `copy`
  module.
- Use the `templates/` folder in the playbook or role directory for the
  `template` module.

These folders allow you to omit the path or use a sub-folder when specifying
files with the `src` argument.

!!! note

    If resources are outside your Ansible playbook or role directory you should use an absolute path with the `src` argument.

!!! warning

    Do not store resources at the same directory level as your Ansible playbook or tasks files.
    Doing this can result in disorganized projects and cause user confusion when distinguishing between resources of the same type, such as YAML.

See
[task paths](https://docs.ansible.com/ansible/latest/playbook_guide/playbook_pathing.html#task-paths)
in the Ansible documentation for more information.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Template a file to /etc/file.conf
      ansible.builtin.template:
        src: ../my_templates/foo.j2 # <- Uses a relative path in the src argument.
        dest: /etc/file.conf
        owner: bin
        group: wheel
        mode: "0644"
```

```yaml
- name: Example playbook
  hosts: all
  vars:
    source_path: ../../my_templates/foo.j2 # <- Sets a variable to a relative path.
  tasks:
    - name: Copy a file to /etc/file.conf
      ansible.builtin.copy:
        src: "{{ source_path }}" # <- Uses the variable in the src argument.
        dest: /etc/foo.conf
        owner: foo
        group: foo
        mode: "0644"
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Template a file to /etc/file.conf
      ansible.builtin.template:
        src: foo.j2 # <- Uses a path from inside templates/ directory.
        dest: /etc/file.conf
        owner: bin
        group: wheel
        mode: "0644"
```

```yaml
- name: Example playbook
  hosts: all
  vars:
    source_path: foo.j2 # <- Uses a path from inside files/ directory.
  tasks:
    - name: Copy a file to /etc/file.conf
      ansible.builtin.copy:
        src: "{{ source_path }}" # <- Uses the variable in the src argument.
        dest: /etc/foo.conf
        owner: foo
        group: foo
        mode: "0644"
```
