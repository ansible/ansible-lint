# internal-names

This rule checks for internal names being used in Ansible content.

Some collections provide content under multiple names. For example, community.general and community.network allow to
reference actions under a long FQCN and a short FQCN. The long FQCN is an implementation detail and must not be used,
as it can change at any time (even in bugfix releases) and using it can render your playbooks and roles nonfunctional.

The `internal-names` rule has the following checks:

- `internal-names[community.general]` - Checks for internal names from the `community.general` collection.
- `internal-names[community.network]` - Checks for internal names from the `community.network` collection.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Create an SSH connection
      community.general.system.ufw: # <- Does use an internal FQCN for the ufw module
        state: enabled
```

## Correct Code

```yaml
- name: Example playbook
  hosts: all
  tasks:
    - name: Create an SSH connection
      community.general.ufw:
        state: enabled
```
