# fqcn

This rule checks the use of fully-qualified collection names (FQCN) inside
ansible content.

```{warning}
Current implementation does not consider the value of `collections:` keys, so
you need to just specify the full name of every action. Collections key was
a transitional mechanism introduced for Ansible 2.9 compatibility and we
recommend you avoid using these as they can easily confuse users and create
bugs when moving some tasks from one location to another.
```

For internal **actions**, if you do not specify the FQCN, Ansible uses the
`ansible.legacy` collection for some modules by default. You can use local
overrides with the `ansible.legacy` collection but not with the
`ansible.builtin` collection.

This rule can generate the following error messages:

- `fqcn[action-internal]` - Use the FQCN for the module known as being builtin.
- `fqcn[action-redirect]` - Replace short action with its FQCN redirect.
- `fqcn[action]` - Use FQCN for any action, to avoid accidents.

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
- name: Example playbook (1st solution)
  hosts: all
  tasks:
    - name: Create an SSH connection
      ansible.legacy.shell: ssh ssh_user@{{ ansible_ssh_host }} -o IdentityFile=path/to/my_rsa # <- This uses the FQCN for the legacy shell module to allow local overrides.
```

```yaml
---
- name: Example playbook (2nd solution)
  hosts: all
  tasks:
    - name: Create an SSH connection
      ansible.builtin.shell: ssh ssh_user@{{ ansible_ssh_host }} # <- This uses the FQCN for the builtin shell module.
```
