(installing-lint)=

# Installing

```{contents} Topics

```

Install Ansible-lint to apply rules and follow best practices with your automation content.

```{note}
Ansible-lint does not currently support installation on Windows systems.
```

For a container image, we recommend using [creator-ee](https://github.com/ansible/creator-ee/), which includes Ansible-lint.
If you have a use case that the `creator-ee` container does satisfy, please contact the team through the [discussions](https://github.com/ansible/ansible-lint/discussions) forum.

You can also run Ansible-lint on your source code with the [Ansible-lint GitHub action](https://github.com/marketplace/actions/ansible-lint) instead of installing it directly.

## Installing the latest version

You can install the most recent version of Ansible-lint with the [pip3] or [pipx] Python package manager.
Use [pipx] to isolate Ansible-lint from your current Python environment as an alternative to creating a virtual environment.

```bash
# This also installs ansible-core if it is not already installed
pip3 install "ansible-lint"
```

## Installing on Fedora and RHEL

You can install Ansible-lint on Fedora, or Red Hat Enterprise Linux (RHEL) with the `dnf` package manager.

```bash
dnf install ansible-lint
```

```{note}
On RHEL, `ansible-lint` package is part of "Red Hat Ansible Automation Platform" subscription, which needs
to be activated.
```

## Installing from source code

**Note**: pip 19.0+ is required for installation from the source repository.
Please consult the [PyPA User Guide] to learn more about managing Pip versions.

```bash
pip3 install git+https://github.com/ansible/ansible-lint.git
```

[installing_from_source]: https://pypi.org/project/pip/
[pip3]: https://pypi.org/project/pip/
[pipx]: https://pypa.github.io/pipx/
[pypa user guide]: https://packaging.python.org/en/latest/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date
