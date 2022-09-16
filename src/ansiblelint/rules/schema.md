# schema

`schema` is a special rule used for the validation of Ansible metadata files
against a set of JSON Schemas. These schemas are restrictive by design, so they
would force the use of only the safe and future-proof syntax, even if Ansible
itself may support a wider range of syntax, mainly for compatibility reasons.

Schema validation happens before almost all the other rules and passing it is
required for processing the other rules. The main reason for this decision is
to prevent various rules from reporting weird errors, just because the syntax
was not the expected one. Nobody wants to see an explosion of rule violations
that are caused by a single typo in the linted file.

This rule is **not skippable** and you cannot use inline `noqa` comments to
ignore it.

We are currently checking 12 schemas and most of them are maintained
by a separate project [ansible/schemas](https://github.com/ansible/schemas). If
you find bugs in one of them, please report them directly to their repositories
instead of the ansible-lint project. We do update them very soon after a
change is made to them and plan to make the update process automatic, so a new
release of ansible-lint would not be required when schemas are updated.

The identifier of the schema is mentioned inside brackets after the schema,
keyword, so you will see validation messages for:

- schemas maintained inside the [ansible-lint](https://github.com/ansible/ansible-lint/blob/main/src/ansiblelint/schemas/ansible-lint-config.json) project:
  - `schema[ansible-lint-config]`
- schemas maintained inside the [ansible-navigator](https://github.com/ansible/ansible-navigator) project:
  - `schema[ansible-navigator]` - [ansible-navigator configuration](https://github.com/ansible/ansible-navigator/blob/main/src/ansible_navigator/data/ansible-navigator.json).
- schemas maintained by [schemas](https://github.com/ansible/schemas) project:
  - `schema[arg_specs]` - Ansible [module argument specs](https://docs.ansible.com/ansible/latest/dev_guide/developing_program_flow_modules.html#argument-spec)
  - `schema[execution-environment]` - Ansible [execution environment](https://docs.ansible.com/automation-controller/latest/html/userguide/execution_environments.html#ees)
  - `schema[galaxy]` - Ansible [collection metadata](https://docs.ansible.com/ansible/latest/dev_guide/collections_galaxy_meta.html).
  - `schema[inventory]` - [inventory files](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html), matching `inventory/*.yml`.
  - `schema[meta-runtime]` - [runtime information](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections_structure.html#meta-directory-and-runtime-yml), matching `meta/runtime.yml`
  - `schema[meta]` - metadata for roles, matching `meta/main.yml`, see [role-dependencies](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html#role-dependencies) or [role/metadata.py](https://github.com/ansible/ansible/blob/devel/lib/ansible/playbook/role/metadata.py#L79)) for details.
  - `schema[playbook]` - Ansible playbooks
  - `schema[requirements]` - Ansible [requirements](https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#install-multiple-collections-with-a-requirements-file)), matching `requirements.yml`.
  - `schema[tasks]` - Ansible task files, matching `tasks/**/*.yml`.
  - `schema[vars]` - Ansible [variables](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html), matching `vars/*.yml` and `defaults/*.yml`.

## schema[meta]

It is worth mentioning that, for `meta/main.yml` files, we require you to add a
`version` key that specifies which version to be used, either:

- `1` - for old standalone Ansible roles
- `2` - for new Ansible roles that are contained inside a collection

Ansible does not require this key, but the linter makes it required to avoid
confusion and to be able to provide more specific error messages.

The linter will not allow you to have an empty `meta/main.yml` and files that
only have comments inside do also count as empty. To avoid an error, just add
an explicit version entry to it, like `version: 1`, or remove the file.
