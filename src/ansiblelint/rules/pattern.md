# pattern

This rule aims to validate Ansible pattern directory structure.

## pattern[missing-meta]

`pattern[missing-meta]` is triggered when a pattern.json specification file exists but the required meta directory is missing.

## pattern[missing-playbook]

`pattern[missing-playbook]` is triggered when either the required playbooks directory or playbook file is missing.

## pattern[missing-readme]

`pattern[missing-readme]` is triggered when the README.md file is missing from a pattern directory.

## pattern[name-mismatch]

`pattern[name-mismatch]` is triggered when pattern name does not match with the name key in pattern.json file.
