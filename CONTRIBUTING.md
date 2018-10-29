Contributing to Ansible-lint
============================

To contribute to ansible-lint, please use pull requests on a branch of your own fork.

After [creating your fork on GitHub](https://guides.github.com/activities/forking/), you can do:

```
git clone git@github.com:yourname/ansible-lint
cd ansible-lint
git checkout -b your-branch-name
DO SOME CODING HERE
git add your new files
git commit --signoff
git push origin your-branch-name
```

Contributors to ansible-lint must agree to [DCO 1.1](./DCO_1_1.md)

You will then be able to create a pull request from your commit.

All fixes to core functionality (i.e. anything except rules or examples) should
be accompanied by tests that fail prior to your change and succeed afterwards.

Feel free to raise issues in the repo if you don't feel able to contribute a code fix.

Standards
---------

ansible-lint is flake8 compliant with `max-line-length` set to 100
(see [setup.cfg](setup.cfg)).

ansible-lint works with both Ansible 1.9 and Ansible 2.0 onwards. This will be
the case for the foreseeable future, so please ensure all contributions work
with both.

Automated tests will be run against all PRs for flake8 compliance and Ansible
compatibility - to check before pushing commits, just use `tox`.

Talk to us
----------

Discussion around ansible-lint happens in `#ansible-galaxy` IRC channel on Freenode and the [Ansible Development List](https://groups.google.com/forum/#!forum/ansible-devel)

For the full list of Ansible IRC and Mailing list, please see the [Ansible Communication](https://docs.ansible.com/ansible/latest/community/communication.html) page
Release announcements will be made to the [Ansible Announce](https://groups.google.com/forum/#!forum/ansible-announce) list.

Possible security bugs should be reported via email to `security@ansible.com`

Code of Conduct
---------------

As with all Ansible projects, we have a [Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
