# Autofix

Ansible-lint autofix can fix or simplify fixing issues identified by that rule. `ansible-lint --fix` will reformat YAML files and run transform for the given
rules. You can limit the effective rule transforms (the 'write_list') by passing
a keywords 'all' or 'none' or a comma separated list of rule ids or rule tags.
By default it will run all transforms (effectively `write_list: ["all"]`).
You can disable running transforms by setting `write_list: ["none"]`. Or only enable a subset of rule transforms by listing rules/tags here.

Following is the list of supported rules covered under autofix functionality.

{!_autofix_rules.md!}
