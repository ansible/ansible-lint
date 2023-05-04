# schema

The `schema` rule validates Ansible metadata files against JSON schemas. These
schemas ensure the compatibility of Ansible syntax content across versions.

This `schema` rule is **mandatory**. You cannot use inline `noqa` comments to
ignore it.

Ansible-lint validates the `schema` rule before processing other rules. This
prevents unexpected syntax from triggering multiple rule violations.

## Validated schema

Ansible-lint currently validates several schemas that are maintained in separate
projects and updated independently to ansible-lint.

> Report bugs related to schema in their respective repository and not in the
> ansible-lint project.

Maintained in the [ansible-lint](https://github.com/ansible/ansible-lint)
project:

- `schema[ansible-lint-config]` validates
  [ansible-lint configuration](https://github.com/ansible/ansible-lint/blob/main/src/ansiblelint/schemas/ansible-lint-config.json)
- `schema[role-arg-spec]` validates
  [role argument specs](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#specification-format)
  which is a little bit different than the module argument spec.
- `schema[execution-environment]` validates
  [execution environments](https://docs.ansible.com/automation-controller/latest/html/userguide/execution_environments.html)
- `schema[galaxy]` validates
  [collection metadata](https://docs.ansible.com/ansible/latest/dev_guide/collections_galaxy_meta.html).
- `schema[inventory]` validates
  [inventory files](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html)
  that match `inventory/*.yml`.
- `schema[meta-runtime]` validates
  [runtime information](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections_structure.html#meta-directory-and-runtime-yml)
  that matches `meta/runtime.yml`
- `schema[meta]` validates metadata for roles that match `meta/main.yml`. See
  [role-dependencies](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#role-dependencies)
  or
  [role/metadata.py](https://github.com/ansible/ansible/blob/devel/lib/ansible/playbook/role/metadata.py#L79))
  for details.
- `schema[playbook]` validates Ansible playbooks.
- `schema[requirements]` validates Ansible
  [requirements](https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#install-multiple-collections-with-a-requirements-file)
  files that match `requirements.yml`.
- `schema[tasks]` validates Ansible task files that match `tasks/**/*.yml`.
- `schema[vars]` validates Ansible
  [variables](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html)
  that match `vars/*.yml` and `defaults/*.yml`.

Maintained in the
[ansible-navigator](https://github.com/ansible/ansible-navigator) project:

- `schema[ansible-navigator]` validates
  [ansible-navigator configuration](https://github.com/ansible/ansible-navigator/blob/main/src/ansible_navigator/data/ansible-navigator.json)

## schema[meta]

For `meta/main.yml` files, Ansible-lint requires a `galaxy_info.standalone`
property that clarifies if a role is an old standalone one or a new one,
collection based:

```yaml
galaxy_info:
  standalone: true # <-- this is a standalone role (not part of a collection)
```

Ansible-lint requires the `standalone` key to avoid confusion and provide more
specific error messages. For example, the `meta` schema will require some
properties only for standalone roles or prevent the use of some properties that
are not supported by collections.

You cannot use an empty `meta/main.yml` file or use only comments in the
`meta/main.yml` file.

## schema[moves]

These errors usually look like "foo was moved to bar in 2.10" and indicate
module moves between Ansible versions.
