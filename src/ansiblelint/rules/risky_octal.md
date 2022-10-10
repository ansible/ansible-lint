# risky-octal

This rule checks that octal file permissions either contain a leading zero or are a string value.

Modules that are checked:

- [`ansible.builtin.assemble`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/assemble_module.html)
- [`ansible.builtin.copy`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html)
- [`ansible.builtin.file`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html)
- [`ansible.builtin.replace`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/replace_module.html)
- [`ansible.builtin.template`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html)

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Unsafe example of declaring Numeric file permissions
      ansible.builtin.file:
        path: /etc/foo.conf
        owner: foo
        group: foo
        mode: 644
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Safe example of declaring Numeric file permissions (1st solution)
      ansible.builtin.file:
        path: /etc/foo.conf
        owner: foo
        group: foo
        mode: 0644 # <- Leading zero will prevent Numeric file permissions to behave in unexpected ways.
    - name: Safe example of declaring Numeric file permissions (2nd solution)
      ansible.builtin.file:
        path: /etc/foo.conf
        owner: foo
        group: foo
        mode: "644" # <- Being in a string will prevent Numeric file permissions to behave in unexpected ways.
```
