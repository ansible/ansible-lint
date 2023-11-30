# package-latest

This rule checks that package managers install software in a controlled, safe manner.

Package manager modules, such as `ansible.builtin.yum`, include a `state` parameter that configures how Ansible installs software.
In production environments, you should set `state` to `present` and specify a target version to ensure that packages are installed to a planned and tested version.

Setting `state` to `latest` not only installs software, it performs an update and installs additional packages.
This can result in performance degradation or loss of service.
If you do want to update packages to the latest version, you should also set the `update_only` or `only_upgrade` parameter to `true` based on package manager to avoid installing additional packages.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Install Ansible
      ansible.builtin.yum:
        name: ansible
        state: latest # <- Installs the latest package.

    - name: Install Ansible-lint
      ansible.builtin.pip:
        name: ansible-lint
      args:
        state: latest # <- Installs the latest package.

    - name: Install some-package
      ansible.builtin.package:
        name: some-package
        state: latest # <- Installs the latest package.

    - name: Install sudo with update_only to false
      ansible.builtin.yum:
        name: sudo
        state: latest
        update_only: false # <- Updates and installs packages.

    - name: Install sudo with only_upgrade to false
      ansible.builtin.apt:
        name: sudo
        state: latest
        only_upgrade: false # <- Upgrades and installs packages
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Install Ansible
      ansible.builtin.yum:
        name: ansible-2.12.7.0
        state: present # <- Pins the version to install with yum.

    - name: Install Ansible-lint
      ansible.builtin.pip:
        name: ansible-lint
      args:
        state: present
        version: 5.4.0 # <- Pins the version to install with pip.

    - name: Install some-package
      ansible.builtin.package:
        name: some-package
        state: present # <- Ensures the package is installed.

    - name: Update sudo with update_only to true
      ansible.builtin.yum:
        name: sudo
        state: latest
        update_only: true # <- Updates but does not install additional packages.

    - name: Install sudo with only_upgrade to true
      ansible.builtin.apt:
        name: sudo
        state: latest
        only_upgrade: true # <- Upgrades but does not install additional packages.
```
