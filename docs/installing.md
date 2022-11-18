(installing-lint)=

# Installation methods

```{contents} Topics

```

Install Ansible-lint to apply rules and follow best practices with your automation content.

```{note}
Ansible-lint does not currently support installation on Windows systems.
```

For a container image, we recommend using [creator-ee](https://github.com/ansible/creator-ee/), which includes Ansible-lint.
If you have a use case that the `creator-ee` container does satisfy, please contact the team through the [discussions](https://github.com/ansible/ansible-lint/discussions) forum.

You can also run Ansible-lint on your source code with the [Ansible-lint GitHub action](https://github.com/marketplace/actions/ansible-lint) instead of installing it directly.

```{toctree}
:maxdepth: 1

installing_pip
installing_dnf
installing_source

```
