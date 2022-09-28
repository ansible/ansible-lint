# fqcn

This rule checks for fully-qualified collection names (FQCN) in Ansible content.

Declaring an FQCN ensures that an action uses code from the correct namespace.
This avoids ambiguity and conflicts that can cause operations to fail or produce unexpected results.

The `fqcn` rule has the following checks:

- `fqcn[action]` - Checks all actions for FQCNs.
- `fqcn[action-core]` - Checks for FQCNs from the `ansible.legacy` or `ansible.builtin` collection.
- `fqcn[action-redirect]` - Provides the correct FQCN to replace short actions.

```{note}
In most cases you should declare the `ansible.builtin` collection for internal Ansible actions.
You should declare the `ansible.legacy` collection if you use local overrides with actions, such with as the ``shell`` module.
```

```{warning}
This rule does not take [`collections` keyword](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#simplifying-module-names-with-the-collections-keyword) into consideration.
The `collections` keyword provided a temporary mechanism transitioning to Ansible 2.9.
You should rewrite any content that uses the `collections:` key and avoid it where possible.
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Create an SSH connection
      shell: ssh ssh_user@{{ ansible_ssh_host }} # <- Does not use the FQCN for the shell module.
```

## Correct Code

```yaml
---
- name: Example playbook (1st solution)
  hosts: all
  tasks:
    - name: Create an SSH connection
      # Use the FQCN for the legacy shell module and allow local overrides.
      ansible.legacy.shell: ssh ssh_user@{{ ansible_ssh_host }} -o IdentityFile=path/to/my_rsa
```

```yaml
---
- name: Example playbook (2nd solution)
  hosts: all
  tasks:
    - name: Create an SSH connection
      # Use the FQCN for the builtin shell module.
      ansible.builtin.shell: ssh ssh_user@{{ ansible_ssh_host }}
```
