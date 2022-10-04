# no-relative-paths

This rule checks for relative paths in the `ansible.builtin.copy` and `ansible.builtin.template` modules.

Relative paths in a task most often direct Ansible to remote files and directories on managed nodes.
In the `ansible.builtin.copy` and `ansible.builtin.template` modules, the `src` argument refers to local files and directories on the control node.
For this reason you should always provide an absolute path to resources with the `src` argument.

See [task paths](https://docs.ansible.com/ansible/latest/user_guide/playbook_pathing.html#task-paths) in the Ansible documentation for more information.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Template a file to /etc/file.conf
      ansible.builtin.template:
        src: ../mytemplates/foo.j2 # <- Uses a relative path in the src argument.
        dest: /etc/file.conf
        owner: bin
        group: wheel
        mode: "0644"
```

```yaml
- name: Example playbook
  hosts: all
  vars:
    source_path: ../../mytemplates/foo.j2 # <- Sets a variable to a relative path.
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
        src: /path/to/mytemplates/foo.j2 # <- Uses an absolute path in the src argument.
        dest: /etc/file.conf
        owner: bin
        group: wheel
        mode: "0644"
```

```yaml
- name: Example playbook
  hosts: all
  vars:
    source_path: /path/to/mytemplates/foo.j2 # <- Sets a variable to an absolute path.
  tasks:
    - name: Copy a file to /etc/file.conf
      ansible.builtin.copy:
        src: "{{ source_path }}" # <- Uses the variable in the src argument.
        dest: /etc/foo.conf
        owner: foo
        group: foo
        mode: "0644"
```
