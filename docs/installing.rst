
.. _installing_lint:


**********
Installing
**********

.. contents:: Topics

Installing on Windows is not supported because we use symlinks inside Python
packages.

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

Using Pip
---------

.. code-block:: bash

    # Assuming you already installed ansible and you also want the optional
    # yamllint support:
    pip install "ansible-lint[yamllint]"

    # If you want to install and use latest ansible (w/o community collections)
    pip install "ansible-lint[core,yamllint]"

    # If you want to install and use latest ansible with community collections
    pip install "ansible-lint[community,yamllint]"

    # If you want to install an older version of Ansible 2.9
    pip install ansible-lint "ansible>=2.9,<2.10"

.. _installing_from_source:

From Source
-----------

**Note**: pip 19.0+ is required for installation. Please consult with the
`PyPA User Guide`_ to learn more about managing Pip versions.

.. code-block:: bash

    pip install git+https://github.com/ansible-community/ansible-lint.git

.. _PyPA User Guide: https://packaging.python.org/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date
