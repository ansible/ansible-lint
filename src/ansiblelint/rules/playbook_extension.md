# playbook-extension

This rule checks the file extension for playbooks is either `.yml` or `.yaml`.
Ansible playbooks are expressed in YAML format with minimal syntax.

The [YAML syntax](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html#yaml-syntax) reference provides additional detail.

## Problematic Code

This rule is triggered if Ansible playbooks do not have a file extension or use an unsupported file extension such as `playbook.json` or `playbook.xml`.

## Correct Code

Save Ansible playbooks as valid YAML with the `.yml` or `.yaml` file extension.
