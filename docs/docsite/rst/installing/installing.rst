
.. _installing_lint:


**********
Installing
**********

.. contents:: Topics

This topic describes how to install Ansible Lint.

.. _installing_with_pip:

Using Pip
=========

.. code-block:: bash

    $ pip install ansible-lint

.. _installing_from_source:

From Source
===========

.. code-block:: bash

    $ git clone https://github.com/ansible/ansible-lint
    $ export PYTHONPATH=$PYTHONPATH:`pwd`/ansible-lint/lib
    $ export PATH=$PATH:`pwd`/ansible-lint/bin
