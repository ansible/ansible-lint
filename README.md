[![PyPI version](https://img.shields.io/pypi/v/ansible-lint.svg)](https://pypi.org/project/ansible-lint)
[![Ansible-lint rules explanation](https://img.shields.io/badge/Ansible--lint-rules-blue.svg)](https://ansible.readthedocs.io/projects/lint/rules/)
[![Discussions](https://img.shields.io/badge/Discussions-gray.svg)](https://forum.ansible.com/tag/ansible-lint)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

# Ansible-lint

`ansible-lint` checks playbooks for practices and behavior that could
potentially be improved. As a community-backed project ansible-lint supports
only the last two major versions of Ansible.

[Visit the Ansible Lint docs site](https://ansible.readthedocs.io/projects/lint/)

# Using ansible-lint as a GitHub Action

This action allows you to run `ansible-lint` on your codebase without having to
install it yourself.

```yaml
# .github/workflows/ansible-lint.yml
name: ansible-lint
on:
  pull_request:
    branches: ["main", "stable", "release/v*"]
jobs:
  build:
    name: Ansible Lint # Naming the build is important to use it as a status check
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - name: Run ansible-lint
        uses: ansible/ansible-lint@main # or vX.X.X version
        # optional (see below):
        with:
          args: ""
          gh_action_ref: "<version - e.g. `v25.5.0`>" # Not recommended for non-composite action use
          setup_python: "true"
          working_directory: ""
          requirements_file: ""
```

By default, the workflow uses ansible-lint installed from `main`. For production or stable workflows, it is recommended to specify a particular release tag (in format v.X.X.X).

All the arguments are optional:

- `args`: Arguments to be passed to ansible-lint command.
- `gh_action_ref`: The git branch, tag, or commit to use for ansible-lint.
  Not recommended for standard use - only use with composite actions where
  `GH_ACTION_REF` is set to the parent action version.
- `requirements_file`: Path to the requirements.yml file to install role and
  collection dependencies.
- `setup_python`: If python should be installed. Default is `true`.
- `working_directory`: The directory where to run ansible-lint from. Default is
  `github.workspace`. Needed if you want to lint only a subset of
  your repository.


For more details, see [ansible-lint-action].

# Communication

Refer to the
[Talk to us](https://ansible.readthedocs.io/projects/lint/contributing/#talk-to-us)
section of the Contributing guide to find out how to get in touch with us.

You can also find more information in the
[Ansible communication guide](https://docs.ansible.com/ansible/devel/community/communication.html).

# Contributing

Please read [Contribution guidelines] if you wish to contribute.

# Code of Conduct

Please see the
[Ansible Community Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html).

# Licensing

The ansible-lint project is distributed as [GPLv3] due to use of [GPLv3] runtime
dependencies, like `ansible` and `yamllint`.

For historical reasons, its own code-base remains licensed under a more liberal
[MIT] license and any contributions made are accepted as being made under
original [MIT] license.

# Authors

ansible-lint was created by [Will Thames] and is now maintained as part of the [Ansible]
by [Red Hat] project.

[ansible]: https://ansible.com
[contribution guidelines]:
  https://ansible.readthedocs.io/projects/lint/contributing
[gplv3]: https://github.com/ansible/ansible-lint/blob/main/COPYING
[mit]:
  https://github.com/ansible/ansible-lint/blob/main/docs/licenses/LICENSE.mit.txt
[red hat]: https://redhat.com
[will thames]: https://github.com/willthames
[ansible-lint-action]:
  https://ansible.readthedocs.io/projects/lint/installing/#installing-from-source-code
