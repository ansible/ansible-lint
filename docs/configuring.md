# Configuration

Customize how Ansible-lint runs against automation content to suit your needs.
You can ignore certain rules, enable `opt-in` rules, and control various other
settings.

Ansible-lint loads configuration from a file in the current working directory or
from a file that you specify in the command line. If you provide configuration
on both via a config file and on the command line, list values are merged (for
example `exclude_paths`) and **True** is preferred for boolean values like
`quiet`.

## Using local configuration files

Specify Ansible-lint configuration in either `.ansible-lint` or
`.config/ansible-lint.yml` in your current working directory.

!!! note

    If Ansible-lint cannot find a configuration file in the current directory it attempts to locate it in a parent directory.
    However Ansible-lint does not try to load configuration that is outside the git repository.

## Specifying configuration files

Use the `-c <filename>` CLI flag with command line invocations of Ansible-lint,
for example:

```bash
ansible-lint -c path/to/ansible-lint-dev.yml
```

## Ansible-lint configuration

The following values are supported, and function identically to their CLI
counterparts:

```yaml
{!../.ansible-lint!}
```

## Ignoring rules for entire files

Ansible-lint will load skip rules from an `.ansible-lint-ignore` or
`.config/ansible-lint-ignore.txt` file that should reside adjacent to the config
file. The file format is very simple, containing the filename and the rule to be
ignored. It also supports comments starting with `#`.

```yaml title=".ansible-lint-ignore"
# this is just a comment
playbook.yml package-latest # disable package-latest rule for playbook.yml
playbook.yml deprecated-module
```

The file can also be created by adding `--generate-ignore` to the command line.
Keep in mind that this will override any existing file content.

## Pre-commit setup

To use Ansible-lint with [pre-commit], add the following to the
`.pre-commit-config.yaml` file in your local repository.

Change **rev:** to either a commit sha or tag of Ansible-lint that contains
`.pre-commit-hooks.yaml`.

```yaml
- repo: https://github.com/ansible/ansible-lint
  rev: ... # put latest release tag from https://github.com/ansible/ansible-lint/releases/
  hooks:
    - id: ansible-lint
```

[pre-commit]: https://pre-commit.com/
