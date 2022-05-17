# Contributing to Ansible-lint

To contribute to ansible-lint, please use pull requests on a branch
of your own fork.

After [creating your fork on GitHub], you can do:

```shell-session
$ git clone git@github.com:your-name/ansible-lint
$ cd ansible-lint
$ git checkout -b your-branch-name
# DO SOME CODING HERE
$ git add your new files
$ git commit -v
$ git push origin your-branch-name
```

You will then be able to create a pull request from your commit.

All fixes to core functionality (i.e. anything except docs or examples)
should be accompanied by tests that fail prior to your change and
succeed afterwards.

Feel free to raise issues in the repo if you feel unable to
contribute a code fix.

## Standards

ansible-lint is flake8 compliant with **max-line-length** set to 100.

ansible-lint works only with supported Ansible versions at the time it was released.

Automated tests will be run against all PRs for flake8 compliance
and Ansible compatibility — to check before pushing commits, just
use [tox](https://tox.wiki/).

% DO-NOT-REMOVE-deps-snippet-PLACEHOLDER

## Talk to us

Use Github [discussions] forum or for a live chat experience try
`#ansible-devtools` IRC channel on libera.chat or Matrix room
[#devtools:ansible.com](https://matrix.to/#/#devtools:ansible.com).

For the full list of Ansible IRC and Mailing list, please see the
[Ansible Communication] page.
Release announcements will be made to the [Ansible Announce] list.

Possible security bugs should be reported via email
to <mailto:security@ansible.com>.

## Code of Conduct

As with all Ansible projects, we have a [Code of Conduct].

[.flake8]: https://github.com/ansible-community/ansible-lint/blob/main/.flake8
[ansible announce]: https://groups.google.com/forum/#!forum/ansible-announce
[ansible communication]: https://docs.ansible.com/ansible/latest/community/communication.html
[code of conduct]: https://docs.ansible.com/ansible/latest/community/code_of_conduct.html
[creating your fork on github]: https://guides.github.com/activities/forking/
[discussions]: https://github.com/ansible-community/ansible-lint/discussions
[supported ansible versions]: https://docs.ansible.com/ansible-core/devel/reference_appendices/release_and_maintenance.html#ansible-core-release-cycle
[tox]: https://tox.readthedocs.io
