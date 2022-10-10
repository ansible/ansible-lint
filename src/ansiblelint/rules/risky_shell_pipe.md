# risky-shell-pipe

This rule checks for the bash `pipefail` option with the Ansible `shell` module.

You should always set `pipefail` when piping output from the `shell` module to another command.
The return status of a pipeline is the exit status of the command in the `shell` module.
The `pipefail` option ensures that tasks fail as expected if the first command fails.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Pipeline without pipefail
      shell: false | cat
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  become: no
  tasks:
    - name: Pipeline with pipefail
      shell: set -o pipefail && false | cat

    - name: Pipeline with pipefail, multi-line
      shell: |
        set -o pipefail
        false | cat
```
