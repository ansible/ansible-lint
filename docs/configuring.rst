
.. _configuring_lint:

***********
Configuring
***********

.. contents:: Topics

Configuration File
------------------

Ansible-lint supports local configuration via a ``.ansible-lint`` configuration
file. Ansible-lint checks the working directory for the presence of this file
and applies any configuration found there. The configuration file location can
also be overridden via the ``-c path/to/file`` CLI flag.

When configuration file is not found in current directory, the tool will try
to look for one in parent directories but it will not go outside current git
repository.

If a value is provided on both the command line and via a config file, the
values will be merged (if a list like **exclude_paths**), or the **True** value
will be preferred, in the case of something like **quiet**.

The following values are supported, and function identically to their CLI
counterparts:

.. literalinclude:: ../.ansible-lint
  :language: yaml

Pre-commit Setup
----------------

To use ansible-lint with `pre-commit`_, just add the following to your local
repo's ``.pre-commit-config.yaml`` file. Make sure to change **rev:** to be
either a git commit sha or tag of ansible-lint containing ``hooks.yaml``.

.. code-block:: yaml

    - repo: https://github.com/ansible-community/ansible-lint.git
      rev: ...  # put latest release tag from https://github.com/ansible-community/ansible-lint/releases/
      hooks:
        - id: ansible-lint
          files: \.(yaml|yml)$

.. _pre-commit: https://pre-commit.com
