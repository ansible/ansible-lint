# template-instead-of-copy

This rule identifies the presence of variable interpolation inside `copy`
module and recommends instead the use of the `template` module. This is based on
the official [recommendation](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html#synopsis)
from Ansible documentation.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Write file content
      ansible.builtin.copy:
        content: "Some {{ foo }}" # <-- should use template instead
        dest: /tmp/foo.txt
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Write file content
      ansible.builtin.template:
        src: foo.txt.j2
        dest: /tmp/foo.txt
```

Also, create a file `templates/foo.txt.j2` with `Some {{ foo }}` as its content.
