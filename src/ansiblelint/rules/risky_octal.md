# risky-octal

This rule checks that octal file permissions are strings that contain a leading
zero or are written in
[symbolic modes](https://www.gnu.org/software/findutils/manual/html_node/find_html/Symbolic-Modes.html),
such as `u+rwx` or `u=rw,g=r,o=r`.

Using integers or octal values in YAML can result in unexpected behavior. For
example, the YAML loader interprets `0644` as the decimal number `420` but
putting `644` there will produce very different results.

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
        mode: "0644" # <- quoting and the leading zero will prevent surprises
        # "0o644" is also a valid alternative.
```
