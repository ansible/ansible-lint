GitHub Actions Workflows
------------------------

We used to have GitHub Actions Workflows configured and running smoothly
up until November 13, 2019. But not anymore.


Current state
=============

GitHub Actions are disabled because GitHub doesn't support them for
legacy plan that Ansible organization has at the moment.

Refs:

- https://github.com/ansible/community/issues/505
- https://github.com/ansible/ansible-lint/pull/633
- https://twitter.com/webKnjaZ/status/1194964915506831362


Reverting
=========

Whenever the problem is solved (either by moving ansible-lint to another
organization or a billing plan), this change should be reverted.

To do this, it should be enough to reopen and merge the following PR:

- https://github.com/ansible/ansible-lint/pull/637
