# fqcn

This rule checks for fully-qualified collection names (FQCN) in Ansible content.

Declaring an FQCN ensures that an action uses code from the correct namespace.
This avoids ambiguity and conflicts that can cause operations to fail or produce
unexpected results.

The `fqcn` rule has the following checks:

- `fqcn[action]` - Use FQCN for module actions, such ...
- `fqcn[action-core]` - Checks for FQCNs from the `ansible.legacy` or
  `ansible.builtin` collection.
- `fqcn[canonical]` - You should use canonical module name ... instead of ...
- `fqcn[keyword]` - Avoid `collections` keyword by using FQCN for all plugins,
  modules, roles and playbooks.

!!! note

    In most cases you should declare the `ansible.builtin` collection for internal Ansible actions.
    You should declare the `ansible.legacy` collection if you use local overrides with actions, such with as the ``shell`` module.

!!! warning

    This rule does not take [`collections` keyword](https://docs.ansible.com/ansible/latest/collections_guide/collections_using_playbooks.html#simplifying-module-names-with-the-collections-keyword) into consideration for resolving content.
    The `collections` keyword provided a temporary mechanism transitioning to Ansible 2.9.
    You should rewrite any content that uses the `collections:` key and avoid it where possible.

## Canonical module names

Canonical module names are also known as **resolved module names** and they are
to be preferred for most cases. Many Ansible modules have multiple aliases and
redirects, as these were created over time while the content was refactored.
Still, all of them do finally resolve to the same module name, but not without
adding some performance overhead. As very old aliases are at some point removed,
it makes to just refresh the content to make it point to the current canonical
name.

The only exception for using a canonical name is if your code still needs to be
compatible with a very old version of Ansible, one that does not know how to
resolve that name. If you find yourself in such a situation, feel free to add
this rule to the ignored list.

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
      ansible.legacy.shell:
        ssh ssh_user@{{ ansible_ssh_host }} -o IdentityFile=path/to/my_rsa
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
