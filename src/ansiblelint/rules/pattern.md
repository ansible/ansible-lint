# pattern

This rule aims to validate Ansible pattern directory structure.

## pattern[missing-readme]

`pattern[missing-readme]` is triggered when the README.md file is missing from a pattern directory.

## pattern[missing-meta]

`pattern[missing-meta]` is triggered when a pattern.json specification file exists but the required meta directory is missing.

## pattern[missing-playbook]

`pattern[missing-playbook]` is triggered when either the required playbooks directory or playbook file is missing.
 
pattern[missing-] rule that triggers when pattern.json "name" does not matches with pattern name.
"name": "my_pattern",
