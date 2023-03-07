# Schemas for Ansible and its related tools

[![ci](https://github.com/ansible-community/schemas/actions/workflows/task.yml/badge.svg)](https://github.com/ansible-community/schemas/actions/workflows/task.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Repository License: MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

## About Schemas

This project aims to generate JSON/YAML validation schemas for Ansible files
such as playbooks, tasks, requirements, meta or vars and also for Molecule
configuration.

Keep in mind that these schemas will limit your freedom of choice regarding the
syntax you can use to write Ansible tasks as they do not allow some historical
forms which are still allowed by Ansible itself.

Not any file accepted by Ansible will pass these schemas but we do expect that
any file that passed these schemas should be accepted by Ansible.

- YAML 1.2 booleans are required as `true` or `false`, while Ansible itself
  allows you to use more relaxed forms like `yes` or `no`.
- Inline actions are not allowed, as schema cannot validate them
- Non-built-in modules must be called using `action:` blocks
- Module arguments are not yet verified but we plan to implement it
- Out schemas are strict about usage of jinja2 templating and require `{{` on
  arguments declared as **explicit**, which forbid the use of `{{` on those
  marked as **implicit**. See the section below for details.

As these schemas are still experimental, creating pull requests to improve the
schema is of much greater help. Though you are still welcome to report bugs but
expect them to take a long time until someone finds time to fix them.

If you want to help improve the schemas, have a look at the
[development documentation](CONTRIBUTING.md).

## Schema Bundle

We are currently migrating towards a single [ansible.json](/f/ansible.json)
schema bundle, one that contains subschema definitions for all the supported
file types.

To configure your validator or editor to use the bundle, use the new URLs below,
the part after the `#` in the URLs is essential for informing the loader about
which subschema to use. You can also look at our
[settings.json](.vscode/settings.json) to understand how to configure the
[vscode-yaml](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
extension.

- [playbook subschema url](https://raw.githubusercontent.com/ansible/ansible-lint/main/src/ansiblelint/schemas/ansible.json#/$defs/playbook)
- [tasks subschema uri](https://raw.githubusercontent.com/ansible/ansible-lint/main/src/ansiblelint/schemas/ansible.json#/$defs/tasks)

## Jinja2 implicit vs explicit templating

While Ansible might allow you to combine implicit and explicit templating, our
schema will not. Our schemas will only allow you to use the recommended form,
either by forbidding you to use the curly braces on implicit ones or forcing you
to add them on explicit ones.

Examples:

```yaml
- name: some task
  command: echo 123
  register: result
  vars:
    become_method_var: sudo
  become_method: become_method_var # <-- schema will not allow this
  # become_method: "{{ become_method_var }}" # <-- that is allowed
```

### How to find if a field is implicit or explicit?

Run assuming that your keyword is `no_log`, you can run
`ansible-doc -t keyword no_log`, which will give you the following output:

```yaml
failed_when:
  applies_to:
    - Task
  description:
    Conditional expression that overrides the task's normal 'failed' status.
  priority: 0
  template: implicit
  type: list
```

As you can see the `template` field tells you if is implicit or explicit.

Being more restrictive, schema protects you from common accidents, like writing
a simple string in an explicit field. That will always evaluate as true instead
of being evaluated as a jinja template.

## Activating the schemas

At this moment installing
[Ansible VS Code Extension by Red Hat](https://marketplace.visualstudio.com/items?itemName=redhat.ansible)
will activate these schemas. The file patterns used to trigger their use can be
seen
[here](https://github.com/ansible-community/vscode-ansible/blob/master/package.json#L44-L94)

Because these schemas are generic, you can easily use them with any validators
that support them.
