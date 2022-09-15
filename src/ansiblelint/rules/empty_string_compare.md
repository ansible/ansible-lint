# empty-string-compare

This rule checks for empty string comparison in playbooks.
To ensure code clarity you should avoid using empty strings in conditional statements with the `when` clause.

- Use `when: var | length > 0` instead of `when: var != ""`.
- Use `when: var | length == 0` instead of `when: var == ""`.

This is an opt-in rule.
You must enable it in your Ansible-lint configuration as follows:

```yaml
enable_list:
  - empty-string-compare
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Shut down
      ansible.builtin.command: /sbin/shutdown -t now
      when: ansible_os_family == "" # <- Compares with an empty string.
    - name: Shut down
      ansible.builtin.command: /sbin/shutdown -t now
      when: ansible_os_family !="" # <- Compares with an empty string.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Shut down
      ansible.builtin.shell: |
        /sbin/shutdown -t now
        echo $var ==
      when: ansible_os_family
```
