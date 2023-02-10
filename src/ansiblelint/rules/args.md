# args

This rule validates if the task arguments conform with the plugin documentation.

The rule validation will check if the option name is valid and has the correct
value along with conditionals on the options like `mutually_exclusive`,
`required_together`, `required_one_of` and so on.

For more information see the
[argument spec validator](https://docs.ansible.com/ansible/latest/reference_appendices/module_utils.html#argumentspecvalidator)
topic in the Ansible module utility documentation.

Possible messages:

- `args[module]` - missing required arguments: ...
- `args[module]` - missing parameter(s) required by ...

## Problematic Code

```yaml
---
- name: Fixture to validate module options failure scenarios
  hosts: localhost
  tasks:
    - name: Clone content repository
      ansible.builtin.git: # <- Required option `repo` is missing.
        dest: /home/www
        accept_hostkey: true
        version: master
        update: false

    - name: Enable service httpd and ensure it is not masked
      ansible.builtin.systemd: # <- Missing 'name' parameter required by 'enabled'.
        enabled: true
        masked: false

    - name: Use quiet to avoid verbose output
      ansible.builtin.assert:
        test:
          - my_param <= 100
          - my_param >= 0
        quiet: invalid # <- Value for option `quiet` is invalid.
```

## Correct Code

```yaml
---
- name: Fixture to validate module options pass scenario
  hosts: localhost
  tasks:
    - name: Clone content repository
      ansible.builtin.git: # <- Contains required option `repo`.
        repo: https://github.com/ansible/ansible-examples
        dest: /home/www
        accept_hostkey: true
        version: master
        update: false

    - name: Enable service httpd and ensure it is not masked
      ansible.builtin.systemd: # <- Contains 'name' parameter required by 'enabled'.
        name: httpd
        enabled: false
        masked: false

    - name: Use quiet to avoid verbose output
      ansible.builtin.assert:
        that:
          - my_param <= 100
          - my_param >= 0
        quiet: True # <- Has correct type value for option `quiet` which is boolean.
```

## Special cases

In some complex cases where you are using jinja expressions, the linter may not
able to fully validate all the possible values and report a false positive. The
example below would usually report
`parameters are mutually exclusive: data|file|keyserver|url` but because we
added `# noqa: args[module]` it will just pass.

```yaml
- name: Add apt keys # noqa: args[module]
  become: true
  ansible.builtin.apt_key:
    url: "{{ zj_item['url'] | default(omit) }}"
    data: "{{ zj_item['data'] | default(omit) }}"
  loop: "{{ repositories_keys }}"
  loop_control:
    loop_var: zj_item
```
