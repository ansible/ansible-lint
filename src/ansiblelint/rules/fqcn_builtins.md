# fqcn-builtins

This rule checks that playbooks use the fully qualified collection name (FQCN) for modules in the `ansible.builtin` collection.

If you do not specify the FQCN, Ansible uses the `ansible.legacy` collection for some modules by default.
You can use local overrides with the `ansible.legacy` collection but not with the `ansible.builtin` collection.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Create an SSH connection
      shell: ssh ssh_user@{{ ansible_ssh_host }} # <- This does not use the FQCN for the shell module.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Create an SSH connection
      ansible.legacy.shell: ssh ssh_user@{{ ansible_ssh_host }} -o IdentityFile=path/to/my_rsa # <- This uses the FQCN for the legacy shell module to allow local overrides.
```

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Create an SSH connection
      ansible.builtin.shell: ssh ssh_user@{{ ansible_ssh_host }} # <- This uses the FQCN for the builtin shell module.
```
