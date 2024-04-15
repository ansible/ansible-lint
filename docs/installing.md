---
# YAML header
render_macros: true
---

# Installing

Install Ansible-lint to apply rules and follow best practices with your
automation content.

!!! note

    Ansible-lint does not currently support installation on Windows systems.

!!! warning

    Ansible-lint does not support any installation methods that are not mentioned in
    this document. Before raising any bugs related to installation, review all of
    the following details:

    - You should use the installation methods outlined in this document only.
    - You should upgrade the Python installer (`pip` or `pipx`) to the latest
      version available from pypi.org. If you use a system package manager, you
      will need to upgrade the installer to a newer version.
    - If you are installing from a git zip archive, which is not supported but
      should work, ensure you use the main branch and the latest version of pip and
      setuptools.
    - If you are installing Ansible-lint within a container or system package, you
      should not report the issue here. Contact the relevant container or package
      provider instead.
    - If you are using [poetry](https://python-poetry.org/), read this
      [discussion](https://github.com/ansible/ansible-lint/discussions/2820#discussioncomment-4400380).

    Pull requests to improve installation instructions are welcome. Any new issues
    related to the installation will be closed and locked.

For a container image, we recommend using
[creator-ee](https://github.com/ansible/creator-ee/) which includes
`ansible-dev-tools` (it combines critical Ansible development packages into a
unified Python package). If you have a use case that the `creator-ee` container
doesn't satisfy, please contact the team through the
[discussion](https://github.com/ansible/ansible-lint/discussions) forum.

You can also run Ansible-lint on your source code with the
[Ansible-lint GitHub action](https://github.com/marketplace/actions/run-ansible-lint)
instead of installing it directly.

## Installing the latest version

{{ install_from_adt("ansible-lint") }}

You can install the most recent version of Ansible-lint with the [pip3] or
[pipx] Python package manager. Use [pipx] to isolate Ansible-lint from your
current Python environment as an alternative to creating a virtual environment.

```bash
# This also installs ansible-core if it is not already installed
pip3 install ansible-lint
```

!!! note

    If you want to install the exact versions of all dependencies that were used to
    test a specific version of ansible-lint, you can add `lock` extra. This will
    only work with Python 3.10 or newer. Do this only inside a virtual environment.

    ```bash
    pip3 install "ansible-lint[lock]"
    ```

## Installing on Fedora and RHEL

You can install Ansible-lint on Fedora, or Red Hat Enterprise Linux (RHEL) with
the `dnf` package manager.

```bash
dnf install ansible-lint
```

!!! note

    On RHEL, `ansible-lint` package is part of "Red Hat Ansible Automation
    Platform" subscription, which needs to be activated.

## Installing from source code

**Note**: `pip>=22.3.1` is required for installation from the source repository.
Please consult the [PyPA User Guide] to learn more about managing Pip versions.

```bash
pip3 install git+https://github.com/ansible/ansible-lint
```

[installing_from_source]: https://pypi.org/project/pip/
[pip3]: https://pypi.org/project/pip/
[pipx]: https://pypa.github.io/pipx/
[pypa user guide]:
  https://packaging.python.org/en/latest/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date

## Installing Ansible Lint as a GitHub Action

To use the action simply create a file `.github/workflows/ansible-lint.yml` with
content similar to the example below:

```yaml
# .github/workflows/ansible-lint.yml
name: ansible-lint
on:
  pull_request:
    branches: ["stable", "release/v*"]
jobs:
  build:
    name: Ansible Lint # Naming the build is important to use it as a status check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run ansible-lint
        uses: ansible/ansible-lint@v6
```

Due to limitations on how GitHub Actions are processing arguments, we do not
plan to provide extra options. You will have to make use of
[ansible-lint own configuration file](https://ansible.readthedocs.io/projects/lint/configuring/)
to alter its behavior.

To also enable [dependabot][dependabot] automatic updates, the newer versions of
ansible-lint action you should create a file similar to
[.github/dependabot.yml][.github/dependabot.yml]

[dependabot]: https://docs.github.com/en/code-security/dependabot
[.github/dependabot.yml]:
  https://github.com/ansible/ansible-lint/blob/main/.github/dependabot.yml#L13-L19
