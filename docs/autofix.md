# Autofix

Ansible-lint autofix can fix or simplify fixing issues identified by that rule. `ansible-lint --fix` will reformat YAML files and run transform for the given
rules. You can limit the effective rule transforms (the 'write_list') by passing
the keywords 'all' or 'none' or a comma separated list of rule ids or rule tags.
By default it will run all transforms (effectively `write_list: ["all"]`).
You can disable running rule-specific transforms by setting
`write_list: ["none"]`. Or only enable a subset of rule transforms by listing
rules/tags here.

The `write_list` controls rule-specific transforms only. YAML reformatting still
runs whenever `--fix` is used, even when `write_list` is set to `["none"]` or
when specific `yaml[...]` rules are listed in `skip_list` or `warn_list`. Run
without `--fix` if you need to keep YAML formatting unchanged.

Following is the list of supported rules covered under autofix functionality.

{!_autofix_rules.md!}
