.. image:: https://img.shields.io/pypi/v/ansible-lint.svg
   :target: https://pypi.org/project/ansible-lint
   :alt: PyPI version

.. image:: https://img.shields.io/badge/Ansible--lint-rules%20table-blue.svg
   :target: https://ansible-lint.readthedocs.io/en/latest/default_rules.html
   :alt: Ansible-lint rules explanation

.. image:: https://img.shields.io/badge/Code%20of%20Conduct-black.svg
   :target: https://docs.ansible.com/ansible/latest/community/code_of_conduct.html
   :alt: Ansible Code of Conduct

.. image:: https://img.shields.io/badge/Discussions-gray.svg
   :target: https://github.com/ansible-community/ansible-lint/discussions
   :alt: Discussions

.. image:: https://github.com/ansible-community/ansible-lint/workflows/gh/badge.svg
   :target: https://github.com/ansible-community/ansible-lint/actions?query=workflow%3Agh+branch%3Amaster+event%3Apush
   :alt: GitHub Actions CI/CD

.. image:: https://img.shields.io/lgtm/grade/python/g/ansible-community/ansible-lint.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/ansible-community/ansible-lint/context:python
   :alt: Language grade: Python

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit


Ansible-lint
============

``ansible-lint`` checks playbooks for practices and behaviour that could
potentially be improved. As a community backed project ansible-lint supports
only the last two major versions of Ansible.

`Visit the Ansible Lint docs site <https://ansible-lint.readthedocs.io/en/latest/>`_

Installing
==========

.. installing-docs-inclusion-marker-do-not-remove

Installing on Windows is not supported because we use symlinks inside Python packages.

While our project does not directly ships a container, the
tool is part of the toolset_ container.  Please avoid raising any bugs
related to containers and use the discussions_ forum instead.

.. code-block:: bash

    # replace docker with podman
    docker run -h toolset -it quay.io/ansible/toolset ansible-lint --version

.. _toolset: https://github.com/ansible-community/toolset
.. _discussions: https://github.com/ansible-community/ansible-lint/discussions

.. note::

    The default installation of ansible-lint package no longer installs any
    specific version of ansible. You need to either install the desired version
    of Ansible yourself or mention one of the helper extras:

    * ``core`` - will install latest version of ansible-base 2.10
    * ``community`` - will install latest version of ansible 2.10 with community collections
    * ``devel`` - will install Ansible from git devel branch (unsupported)

Using Pip
---------

.. code-block:: bash

    # Assuming you already installed ansible:
    pip install ansible-lint

    # If you want to install and use latest ansible (w/o community collections)
    pip install "ansible-lint[core]"

    # If you want to install and use latest ansible with community collections
    pip install "ansible-lint[community]"

    # If you want to install an older version of Ansible 2.9
    pip install ansible-lint "ansible>=2.9,<2.10"

.. _installing_from_source:

From Source
-----------

**Note**: pip 19.0+ is required for installation. Please consult with the `PyPA User Guide`_
to learn more about managing Pip versions.

.. code-block:: bash

    pip install git+https://github.com/ansible-community/ansible-lint.git

.. _PyPA User Guide: https://packaging.python.org/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date

.. installing-docs-inclusion-marker-end-do-not-remove

Configuring
===========

.. configuring-docs-inclusion-marker-do-not-remove

Configuration File
------------------

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
    warn_list:
      - skip_this_tag
      - and_this_one_too
      - skip_this_id
      - '401'


Pre-commit Setup
----------------

To use ansible-lint with `pre-commit`_, just add the following to your local repo's ``.pre-commit-config.yaml`` file. Make sure to change **rev:** to be either a git commit sha or tag of ansible-lint containing ``hooks.yaml``.

.. code-block:: yaml

    - repo: https://github.com/ansible-community/ansible-lint.git
      rev: v4.1.0
      hooks:
        - id: ansible-lint
          files: \.(yaml|yml)$

.. _pre-commit: https://pre-commit.com

.. configuring-docs-inclusion-marker-end-do-not-remove

Contributing
============

Please read `Contribution guidelines`_ if you wish to contribute.

Authors
=======

ansible-lint was created by `Will Thames`_ and is now maintained as part of the `Ansible`_ by `Red Hat`_ project.

.. _Contribution guidelines: https://ansible-lint.readthedocs.io/en/latest/contributing.html
.. _Will Thames: https://github.com/willthames
.. _Ansible: https://ansible.com
.. _Red Hat: https://redhat.com
