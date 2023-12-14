[![PyPI version](https://img.shields.io/pypi/v/ansible-lint.svg)](https://pypi.org/project/ansible-lint)
[![Ansible-lint rules explanation](https://img.shields.io/badge/Ansible--lint-rules-blue.svg)](https://ansible.readthedocs.io/projects/lint/rules/)
[![Discussions](https://img.shields.io/badge/Discussions-gray.svg)](https://github.com/ansible/ansible-lint/discussions)
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
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run ansible-lint
        uses: ansible/ansible-lint@main # or version tag instead of 'main'
```

For more details, see [ansible-lint-action].

# Contributing

Please read [Contribution guidelines] if you wish to contribute.

# Licensing

The ansible-lint project is distributed as [GPLv3] due to use of [GPLv3] runtime
dependencies, like `ansible` and `yamllint`.

For historical reasons, its own code-base remains licensed under a more liberal
[MIT] license and any contributions made are accepted as being made under
original [MIT] license.

# Authors

ansible-lint was created by [Will Thames] and is now maintained as part of the
[Ansible] by [Red Hat] project.

[ansible]: https://ansible.com
[contribution guidelines]: https://ansible.readthedocs.io/projects/lint/contributing
[gplv3]: https://github.com/ansible/ansible-lint/blob/main/COPYING
[mit]:
  https://github.com/ansible/ansible-lint/blob/main/docs/licenses/LICENSE.mit.txt
[red hat]: https://redhat.com
[will thames]: https://github.com/willthames
[ansible-lint-action]:
  https://ansible.readthedocs.io/projects/lint/installing/#installing-from-source-code
