Contributing to Ansible-lint
============================

To contribute to ansible-lint, please use pull requests on a branch
of your own fork.

After `creating your fork on GitHub`_, you can do:

.. code-block:: shell-session

   $ git clone git@github.com:yourname/ansible-lint
   $ cd ansible-lint
   $ git checkout -b your-branch-name
   # DO SOME CODING HERE
   $ git add your new files
   $ git commit -v
   $ git push origin your-branch-name

You will then be able to create a pull request from your commit.

All fixes to core functionality (i.e. anything except docs or examples)
should be accompanied by tests that fail prior to your change and
succeed afterwards.

Feel free to raise issues in the repo if you feel unable to
contribute a code fix.

.. _creating your fork on GitHub:
   https://guides.github.com/activities/forking/

Standards
---------

ansible-lint is flake8 compliant with ``max-line-length`` set to 100
(see `.flake8`_).

ansible-lint works only with `supported Ansible versions`_ at the
time it was released.

Automated tests will be run against all PRs for flake8 compliance
and Ansible compatibility — to check before pushing commits, just
use `tox`_.

.. _.flake8: https://github.com/ansible-community/ansible-lint/blob/master/.flake8
.. _supported Ansible versions:
   https://docs.ansible.com/ansible/devel/reference_appendices
   /release_and_maintenance.html#release-status
.. _tox: https://tox.readthedocs.io

.. DO-NOT-REMOVE-deps-snippet-PLACEHOLDER

Talk to us
----------

Use Github `discussions`_ forum or for a live chat experience try
``#ansible-lint`` IRC channel on libera.chat.

For the full list of Ansible IRC and Mailing list, please see the
`Ansible Communication`_ page.
Release announcements will be made to the `Ansible Announce`_ list.

Possible security bugs should be reported via email
to security@ansible.com.

.. _Ansible Announce:
   https://groups.google.com/forum/#!forum/ansible-announce
.. _discussions:
   https://github.com/ansible-community/ansible-lint/discussions
.. _Ansible Communication:
   https://docs.ansible.com/ansible/latest/community/communication.html

Code of Conduct
---------------

As with all Ansible projects, we have a `Code of Conduct`_.

.. _Code of Conduct:
   https://docs.ansible.com/ansible/latest/community
   /code_of_conduct.html
