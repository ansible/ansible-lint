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

Contributing
============

Please read `Contribution guidelines`_ if you wish to contribute.

Licensing
=========

The code in the ansible-lint repository is licensed under the MIT_ license. If
you contribute to this repository, that license applies to your contributions.

The ansible-lint project also imports the Ansible python module, which is
licensed under the GPLv3_ license. Because of this import, the GPLv3_ rules
apply to the full distribution of ansible-lint. We maintain the MIT_ license on
the repository so we can fully use an MIT_ license in the future if we ever
remove the runtime dependency on Ansible code.

Installing the `ansible-lint` python package does not install any GPL
dependencies, all of them are listed as extras.

Authors
=======

ansible-lint was created by `Will Thames`_ and is now maintained as part of the
`Ansible`_ by `Red Hat`_ project.

.. _Contribution guidelines: https://ansible-lint.readthedocs.io/en/latest/contributing.html
.. _Will Thames: https://github.com/willthames
.. _Ansible: https://ansible.com
.. _Red Hat: https://redhat.com
.. _MIT: https://github.com/ansible-community/ansible-lint/blob/master/LICENSE
.. _GPLv3: https://github.com/ansible/ansible/blob/devel/COPYING
