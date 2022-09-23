# deprecated-module

This rule identifies deprecated modules in playbooks.
You should avoid using deprecated modules because they are not maintained, which can pose a security risk.
Additionally when a module is deprecated it is available temporarily with a plan for future removal.

Refer to the [Ansible module index](https://docs.ansible.com/ansible/latest/collections/index_module.html) for information about replacements and removal dates for deprecated modules.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Configure VLAN ID
      ansible.netcommon.net_vlan: # <- Uses a deprecated module.
        vlan_id: 20
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Configure VLAN ID
      dellemc.enterprise_sonic.sonic_vlans: # <- Uses a platform specific module.
        config:
          - vlan_id: 20
```
