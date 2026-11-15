# deprecated-top-level-facts

This rule reports facts read as top-level `ansible_*` variables, such as
`ansible_hostname` or `ansible_distribution`.

ansible-core 2.20 deprecated injecting facts as top-level variables
(`INJECT_FACTS_AS_VARS`), and ansible-core 2.24 will stop doing it by default.
Read facts from `ansible_facts` instead, without the `ansible_` prefix. This
works with every supported ansible-core version.

The rule checks templated values and conditionals (`when`, `changed_when`,
`failed_when`, `until`, `assert` conditions and `debug` `var`) in tasks, play
variables, variable files and Jinja templates (`.j2`). It also reports facts
read through `hostvars`, like `hostvars[host]['ansible_fqdn']`.

Only facts gathered by the `setup` module are reported. Connection and special
variables that are not facts, like `ansible_host`, `ansible_user`,
`ansible_check_mode` or `ansible_local`, are not reported, and neither are facts
named after a host's network interfaces, like `ansible_eth0`.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Show the hostname
      ansible.builtin.debug:
        msg: "{{ ansible_hostname }}" # <- top-level fact

    - name: Run on Debian only
      ansible.builtin.debug:
        msg: Debian
      when: ansible_os_family == 'Debian' # <- top-level fact
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Show the hostname
      ansible.builtin.debug:
        msg: "{{ ansible_facts['hostname'] }}"

    - name: Run on Debian only
      ansible.builtin.debug:
        msg: Debian
      when: ansible_facts['os_family'] == 'Debian'
```
