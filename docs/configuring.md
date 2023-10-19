# Configuration

Customize how Ansible-lint runs against automation content to suit your needs.
You can ignore certain rules, enable `opt-in` rules, and control various other
settings.

Ansible-lint loads configuration from a file in the current working directory or
from a file that you specify in the command line.

Any configuration option that is passed from the command line will override
the one specified inside the configuration file.

## Using local configuration files

Specify Ansible-lint configuration in either `.ansible-lint`,
`.config/ansible-lint.yml`, or `.config/ansible-lint.yaml` in your current
working directory.

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

To use Ansible-lint with the [pre-commit] tool, add the following to the
`.pre-commit-config.yaml` file in your local repository.

Do not confuse the [pre-commit] tool with the git hook feature that has the same name.
While the [pre-commit] tool can also make use of git hooks, it does not require
them and it does not install them by default.

[pre-commit.ci] is a hosted service that can run pre-commit for you
on each change but you can also run the tool yourself using the CI of your choice.

Change **rev:** to either a commit sha or tag of Ansible-lint that contains
`.pre-commit-hooks.yaml`.

```yaml
---
ci:
  # This section is specific to pre-commit.ci, telling it to create a pull request
  # to update the linter version tag every month.
  autoupdate_schedule: monthly
  # If you have other Ansible collection dependencies (requirements.yml)
  # `pre-commit.ci` will not be able to install them because it runs in offline mode,
  # and you will need to tell it to skip the hook.
  # skip:
  #   - ansible-lint
repos:
- repo: https://github.com/ansible/ansible-lint
  rev: ... # put latest release tag from https://github.com/ansible/ansible-lint/releases/
  hooks:
    - id: ansible-lint
      # Uncomment if you need the full Ansible community bundle instead of ansible-core:
      # additional_dependencies:
      #   - ansible
```

!!! warning

    [pre-commit] always uses python virtual environments. If you happen to
    use the [Ansible package] instead of just [ansible-core] you might be surprised
    to see that pre-commit is not able to find these collections, even if
    your local Ansible does. This is because they are installed inside a location
    that is not available to the virtual environment in which pre-commit hook
    is installed. In this case, you might want to uncomment the commented lines
    from the hook definition above, so the bundle will be installed.

    You should note that collection installed into `~/.ansible` are found by
    the hook.

[pre-commit]: https://pre-commit.com/
[Ansible package]: https://pypi.org/project/ansible/
[ansible-core]: https://pypi.org/project/ansible-core/
[pre-commit.ci]: https://pre-commit.ci/
