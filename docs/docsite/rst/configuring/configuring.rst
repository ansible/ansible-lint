
.. _configuring_lint:

***********
Configuring
***********

.. contents:: Topics

This topic describes how to configure Ansible Lint

Configuration File
==================

Ansible-lint supports local configuration via a ``.ansible-lint`` configuration file. Ansible-lint checks the working directory for the presence of this file and applies any configuration found there. The configuration file location can also be overridden via the ``-c path/to/file`` CLI flag.

If a value is provided on both the command line and via a config file, the values will be merged (if a list like **exclude_paths**), or the **True** value will be preferred, in the case of something like **quiet**.

The following values are supported, and function identically to their CLI counterparts:

.. code-block:: yaml

    exclude_paths:
      - ./my/excluded/directory/
      - ./my/other/excluded/directory/
      - ./last/excluded/directory/
    parseable: true
    quiet: true
    rulesdir:
      - ./rule/directory/
    skip_list:
      - skip_this_tag
      - and_this_one_too
      - skip_this_id
      - '401'
    tags:
      - run_this_tag
    use_default_rules: true
    verbosity: 1


Pre-commit
==========

To use ansible-lint with `pre-commit <http://pre-commit.com>`_, just add the following to your local repo's ``.pre-commit-config.yaml`` file. Make sure to change **sha:** to be either a git commit sha or tag of ansible-lint containing ``hooks.yaml``.

.. code-block:: yaml

    - repo: https://github.com/ansible/ansible-lint.git
      sha: v3.3.1
      hooks:
        - id: ansible-lint
          files: \.(yaml|yml)$
