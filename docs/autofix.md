# Autofix

Ansible-lint autofix can fix or simplify fixing issues identified by that rule. `ansible-lint --fix` will reformat YAML files and run transform for the given
rules. You can limit the effective rule transforms (the 'write_list') by passing
a keywords 'all' or 'none' or a comma separated list of rule ids or rule tags.
By default it will run all transforms (effectively `write_list: ["all"]`).
You can disable running transforms by setting `write_list: ["none"]`. Or only enable a subset of rule transforms by listing rules/tags here.

Following is the list of supported rules covered under autofix functionality.

- [command-instead-of-shell](rules/command-instead-of-shell.md#auto-fixing-capability)
- [deprecated-local-action](rules/deprecated-local-action.md)
- [fqcn](rules/fqcn.md)
- [jinja](rules/jinja.md)
- [key-order](rules/key-order.md)
- [name](rules/name.md)
- [no-free-form](rules/no-free-form.md)
- [no-jinja-when](rules/no-jinja-when.md)
- [no-log-password](rules/no-log-password.md)
- [partial-become](rules/partial-become.md)
