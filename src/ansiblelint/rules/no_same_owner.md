# no-same-owner

This rule checks that the owner and group do not transfer across hosts.

In many cases the owner and group on remote hosts do not match the owner and group assigned to source files.
Preserving the owner and group during transfer can result in errors with permissions or leaking sensitive information.

When you synchronize files, you should avoid transferring the owner and group by setting `owner: false` and `group: false` arguments.
When you unpack archives with the `ansible.builtin.unarchive` module you should set the `--no-same-owner` option.

This is an opt-in rule.
You must enable it in your Ansible-lint configuration as follows:

```yaml
enable_list:
  - no-same-owner
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Synchronize conf file
      ansible.posix.synchronize:
        src: /path/conf.yaml
        dest: /path/conf.yaml # <- Transfers the owner and group for the file.
    - name: Extract tarball to path
      ansible.builtin.unarchive:
        src: "{{ file }}.tar.gz"
        dest: /my/path/ # <- Transfers the owner and group for the file.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Synchronize conf file
      ansible.posix.synchronize:
        src: /path/conf.yaml
        dest: /path/conf.yaml
        owner: false
        group: false # <- Does not transfer the owner and group for the file.
    - name: Extract tarball to path
      ansible.builtin.unarchive:
        src: "{{ file }}.tar.gz"
        dest: /my/path/
        extra_opts:
          - --no-same-owner # <- Does not transfer the owner and group for the file.
```
