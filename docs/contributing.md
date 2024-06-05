# Contributing to Ansible-lint

To contribute to ansible-lint, please use pull requests on a branch of your own
fork.

After [creating your fork on GitHub], you can do:

```shell-session
$ git clone --recursive git@github.com:your-name/ansible-lint
$ cd ansible-lint
$ # Recommended: Initialize and activate a Python virtual environment
$ pip install --upgrade pip
$ pip install -e .[test]       # Install testing dependencies
$ tox run -e lint,pkg,docs,py  # Ensure subset of tox tests work in clean checkout
$ git checkout -b your-branch-name
# DO SOME CODING HERE
$ tox run -e lint,pkg,docs,py  # Ensure subset of tox tests work with your changes
$ git add your new files
$ git commit -v
$ git push origin your-branch-name
```

You will then be able to create a pull request from your commit.

All fixes to core functionality (i.e. anything except docs or examples) should
be accompanied by tests that fail prior to your change and succeed afterwards.

Feel free to raise issues in the repo if you feel unable to contribute a code
fix.

## Standards

ansible-lint works only with supported Ansible versions at the time it was
released.

Automated tests will be run against all PRs, to run checks locally before
pushing commits, just use [tox](https://tox.wiki/en/latest/).

## Talk to us

Use Github [discussions] forum or for a live chat experience try
`#ansible-devtools` IRC channel on libera.chat or Matrix room
[#devtools:ansible.com](https://matrix.to/#/#devtools:ansible.com).

For the full list of Ansible IRC and Mailing list, please see the [Ansible
Communication] page. Release announcements will be made to the [Ansible
Announce] list.

Possible security bugs should be reported via email to
<mailto:security@ansible.com>.

## Code of Conduct

As with all Ansible projects, we have a [Code of Conduct].

[ansible announce]: https://groups.google.com/forum/#!forum/ansible-announce
[ansible communication]:
  https://docs.ansible.com/ansible/latest/community/communication.html
[code of conduct]:
  https://docs.ansible.com/ansible/latest/community/code_of_conduct.html
[creating your fork on github]:
  https://docs.github.com/en/get-started/quickstart/contributing-to-projects
[discussions]: https://github.com/ansible/ansible-lint/discussions
[supported ansible versions]:
  https://docs.ansible.com/ansible-core/devel/reference_appendices/release_and_maintenance.html#ansible-core-release-cycle
[tox]: https://tox.readthedocs.io

## Module dependency graph

Extra care should be taken when considering adding any dependency. Removing most
dependencies on Ansible internals is desired as these can change without any
warning.

```bash exec="1" source="console"
_PIP_USE_IMPORTLIB_METADATA=0 pipdeptree -p ansible-lint
```

## Adding a new rule

Writing a new rule is as easy as adding a single new rule, one that combines
**implementation, testing and documentation**.

One good example is [MetaTagValidRule] which can easily be copied in order to
create a new rule by following the steps below:

- Use a short but clear class name, which must match the filename
- Pick an unused `id`, the first number is used to determine rule section. Look
  at [rules](rules/index.md) page and pick one that matches the best your new
  rule and ee which one fits best.
- Include `experimental` tag. Any new rule must stay as experimental for at
  least two weeks until this tag is removed in next major release.
- Update all class level variables.
- Implement linting methods needed by your rule, these are those starting with
  **match** prefix. Implement only those you need. For the moment you will need
  to look at how similar rules were implemented to figure out what to do.
- Update the tests. It must have at least one test and likely also a negative
  match one.
- If the rule is task specific, it may be best to include a test to verify its
  use inside blocks as well.
- Optionally run only the rule specific tests with a command like:
  {command}`tox -e py -- -k NewRule`
- Run {command}`tox` in order to run all ansible-lint tests. Adding a new rule
  can break some other tests. Update them if needed.
- Run {command}`ansible-lint -L` and check that the rule description renders
  correctly.
- Build the docs using {command}`tox -e docs` and check that the new rule is
  displayed correctly in them.

[metatagvalidrule]:
  https://github.com/ansible/ansible-lint/blob/main/src/ansiblelint/rules/meta_no_tags.py

## Documentation changes

To build the docs, run `tox -e docs`. At the end of the build, you will see the
local location of your built docs.

Building docs locally may not be identical to CI/CD builds. We recommend you to
create a draft PR and check the RTD PR preview page too.

If you do not want to learn the reStructuredText format, you can also
[file an issue](https://github.com/ansible/ansible-lint/issues), and let us know
how we can improve our documentation.
