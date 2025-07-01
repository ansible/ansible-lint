# pattern

This rule aims to validate Ansible pattern directory structure.

## pattern[missing-meta]

`pattern[missing-meta]` is triggered when a pattern.json definition file exists but the parent meta directory (one level up from the pattern.json) is missing.

## pattern[missing-playbook]

`pattern[missing-playbook]` is triggered when either the required playbooks directory or playbook file is missing.

## pattern[missing-readme]

`pattern[missing-readme]` is triggered when the README.md file is missing from a pattern directory.

## pattern[name-mismatch]

`pattern[name-mismatch]` is triggered when the pattern directory name does not match the `name` field value in the pattern.json file.

## Usage

To validate a pattern's directory structure: navigate to the collection directory, run ansible-lint on the pattern definition meta file, and review the validation results:

```bash
cd existing_collection
ansible-lint extensions/patterns/sample_pattern/meta/pattern.json
```

This command will check the pattern directory structure and report any violations found.
