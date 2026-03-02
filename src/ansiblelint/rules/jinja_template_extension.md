# jinja-template-extension

This rule checks that files used with `ansible.builtin.template` have a
`.j2` extension.

Naming template source files with a `.j2` suffix provides several benefits:

- **Editor support**: Editors can apply Jinja2 syntax highlighting
  automatically based on the file extension.
- **Clear intent**: Developers can immediately distinguish template files
  from static files in the `templates/` directory.
- **Convention**: The `.j2` extension is the widely adopted community
  convention for Ansible template files.

This is an opt-in rule.
You must enable it in your Ansible-lint configuration as follows:

```yaml
enable_list:
  - jinja-template-extension
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Deploy config
      ansible.builtin.template:
        src: httpd.conf # <- Missing .j2 extension.
        dest: /etc/httpd/conf/httpd.conf
        mode: "0644"
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Deploy config
      ansible.builtin.template:
        src: httpd.conf.j2 # <- Proper .j2 extension.
        dest: /etc/httpd/conf/httpd.conf
        mode: "0644"
```
