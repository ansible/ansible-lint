# no-relative-paths

This rule checks for relative paths in the `ansible.builtin.copy` and `ansible.builtin.template` modules.

Relative paths in a task most often direct Ansible to remote files and directories on managed nodes.
In the `ansible.builtin.copy` and `ansible.builtin.template` modules, the `src` argument refers to local files and directories on the control node.

```{note}
For `copy` best location to store files is inside `files/` folder within the
playbook/role directory. For `template` the recommended location is `templates/`
folder, also within the playbook/role directory.

For this reason, for `src`, you should either:
- Do not specify a path, or use a sub-folder of either `files/` or `templates/`.
- Use absolute path if the resources are above your Ansible playbook/role
```

```{warning}
Avoid storing files or templates inside the same directory as your playbook or
tasks files. Doing this is a bad practice and also will generate linting
warning in the future. Imagine the user confusion if these files also happen
to be YAML.
```

See [task paths](https://docs.ansible.com/ansible/latest/user_guide/playbook_pathing.html#task-paths) in the Ansible documentation for more information.

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
