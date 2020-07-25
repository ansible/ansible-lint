.. include:: ../.github/CONTRIBUTING.rst
   :end-before: DO-NOT-REMOVE-deps-snippet-PLACEHOLDER

Module dependency graph
-----------------------

Extra care should be taken when considering adding any dependency. Removing
most dependencies on Ansible internals is desired as these can change
without any warning.

.. command-output:: pipdeptree -p ansible-lint

.. include:: ../.github/CONTRIBUTING.rst
   :start-after: DO-NOT-REMOVE-deps-snippet-PLACEHOLDER
