.. image:: https://img.shields.io/pypi/v/ansible-lint.svg
   :target: https://pypi.org/project/ansible-lint
   :alt: PyPI version

.. image:: https://img.shields.io/badge/Ansible--lint-rules%20table-blue.svg
   :target: https://docs.ansible.com/ansible-lint/rules/default_rules.html
   :alt: Ansible-lint rules explanation

.. image:: https://img.shields.io/badge/Code%20of%20Conduct-Ansible-silver.svg
   :target: https://docs.ansible.com/ansible/latest/community/code_of_conduct.html
   :alt: Ansible Code of Conduct

.. image:: https://img.shields.io/badge/Mailing%20lists-Ansible-orange.svg
   :target: https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information
   :alt: Ansible mailing lists

.. image:: https://img.shields.io/travis-ci/com/ansible/ansible-lint/master.svg?label=Linux%20builds%20%40%20Travis%20CI
   :target: https://travis-ci.com/ansible/ansible-lint
   :alt: Travis CI build status


Ansible-lint
============

``ansible-lint`` checks playbooks for practices and behaviour that could
potentially be improved.

Setup
-----

Using pip:

.. code:: bash

    pip install ansible-lint

From source:

.. code:: bash

    pip install git+https://github.com/ansible/ansible-lint.git

Usage
-----

.. code:: console

    Usage: ansible-lint playbook.yml|roledirectory ...

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -L                    list all the rules
      -q                    quieter, although not silent output
      -p                    parseable output in the format of pep8
      -r RULESDIR           specify one or more rules directories using one or
                            more -r arguments. Any -r flags override the default
                            rules in ['/path/to/ansible-
                            lint/lib/ansiblelint/rules'], unless -R is also used.
      -R                    Use default rules ['/path/to/ansible-
                            lint/lib/ansiblelint/rules'] in addition to any extra
                            rules directories specified with -r. There is no need
                            to specify this if no -r flags are used
      -t TAGS               only check rules whose id/tags match these values
      -T                    list all the tags
      -x SKIP_LIST          only check rules whose id/tags do not match these
                            values
      --exclude=EXCLUDE_PATHS
                            path to directories or files to skip. This option is
                            repeatable.
      --force-color         Try force colored output (relying on ansible's code)
      --nocolor             disable colored output
      -c /path/to/file      Specify configuration file to use.  Defaults to
                              ".ansible-lint"

False positives
---------------

Some rules are a bit of a rule of thumb. Advanced git, yum or apt usage,
for example, is typically difficult to achieve through the modules. In
this case, you should mark the task so that warnings aren't produced.

There are two mechanisms for this - one works with all tasks, the other
works with the command checking modules.

Use the ``warn`` parameter with the command or shell module.

Use ``skip_ansible_lint`` tag with any task that you want to skip.

I recommend commenting the reasons why you're skipping the check.
Unfortunately ansible-lint is unable to check for such comments
at this time! (patches welcome)

.. code:: yaml

    - name: this would typically fire CommandsInsteadOfArgumentRule
      command: warn=no chmod 644 X

    - name: this would typically fire CommandsInsteadOfModuleRule
      command: git pull --rebase
      args:
        warn: False

    - name: this would typically fire GitHasVersionRule
      git: src=/path/to/git/repo dest=checkout
      tags:
      - skip_ansible_lint

Rules
-----

Rules are described using a class file per rule.
Default rules are named ``DeprecatedVariableRule.py``, etc.

Each rule definition should have the following:

* ID: A unique identifier
* Short description: Brief description of the rule
* Description: Behaviour the rule is looking for
* Tags: one or more tags that may be used to include or exclude the rule
* At least one of the following methods:
  * ``match`` that takes a line and returns ``None`` or ``False`` if
  the line doesn't match the test and ``True`` or a custom message (this
  allows one rule to test multiple behaviours - see e.g. the
  CommandsInsteadOfModulesRule
  * ``matchtask`` operates on a single task or handler. Such a task
  get standardized to always contain a ``module`` key and
  ``module_arguments`` key. Other common task modifiers such as
  ``when``, ``with_items`` etc. are also available as keys if present
  in the task.

An example rule using ``match`` is:

.. code:: python

    from ansiblelint import AnsibleLintRule

    class DeprecatedVariableRule(AnsibleLintRule):

        id = 'ANSIBLE0001'
        shortdesc = 'Deprecated variable declarations'
        description = 'Check for lines that have old style ${var} ' + \
                      'declarations'
        tags = { 'deprecated' }


        def match(self, file, line):
            return '${' in line

An example rule using ``matchtask`` is:

.. code:: python

    import ansiblelint.utils
    from ansiblelint import AnsibleLintRule

    class TaskHasTag(AnsibleLintRule):
        id = 'ANSIBLE0008'
        shortdesc = 'Tasks must have tag'
        description = 'Tasks must have tag'
        tags = ['productivity']


        def matchtask(self, file, task):
            # If the task include another task or make the playbook fail
            # Don't force to have a tag
            if not set(task.keys()).isdisjoint(['include','fail']):
                return False

            # Task should have tags
            if not task.has_key('tags'):
                  return True

            return False

The ``task` argument to ``matchtask`` contains a number of keys — the critical one is ``action``.
The value of ``task['action']`` contains the module being used, and the arguments passed, both
as key-value pairs and a list of other arguments (e.g. the command used with ``shell``)

In ansible-lint 2.0.0, ``task['action']['args']`` was renamed ``task['action']['module_arguments']``
to avoid a clash when a module actually takes ``args`` as a parameter key (e.g. ``ec2_tag``)

In ansible-lint 3.0.0 ``task['action']['module']`` was renamed
``task['action']['__ansible_module__']`` to avoid a clash when a module take
``module`` as an argument. As a precaution, ``task['action']['module_arguments']``
was renamed ``task['action']['__ansible_arguments__']``

Examples
--------

There are some example playbooks with undesirable features. Running
ansible-lint on them works:

.. code:: bash

    $ ansible-lint examples/example.yml
    [ANSIBLE0004] Git checkouts must contain explicit version
    examples/example.yml:15
    Task/Handler: git check

    [ANSIBLE0004] Git checkouts must contain explicit version
    examples/example.yml:18
    Task/Handler: git check 2

    [ANSIBLE0004] Git checkouts must contain explicit version
    examples/example.yml:30
    Task/Handler: using git module

    [ANSIBLE0002] Trailing whitespace
    examples/example.yml:13
        action: do nothing   

    [ANSIBLE0002] Trailing whitespace
    examples/example.yml:35
        with_items: 

    [ANSIBLE0006] git used in place of git module
    examples/example.yml:24
    Task/Handler: executing git through command

    [ANSIBLE0006] git used in place of git module
    examples/example.yml:27
    Task/Handler: executing git through command

    [ANSIBLE0006] git used in place of git module
    examples/example.yml:30
    Task/Handler: executing git through command

If playbooks include other playbooks, or tasks, or handlers or roles, these
are also handled:

.. code:: bash

    $ bin/ansible-lint examples/include.yml
    [ANSIBLE0004] Checkouts must contain explicit version
    /Users/will/src/ansible-lint/examples/roles/bobbins/tasks/main.yml:3
    action: git a=b c=d

As of version 2.4.0, ansible-lint now works just on roles (this is useful
for CI of roles)

Configuration File
------------------

Ansible-lint supports local configuration via a ``.ansible-lint`` configuration file.  Ansible-lint checks the working directory for the presence of this file and applies any configuration found there.  The configuration file location can also be overridden via the ``-c path/to/file`` CLI flag.

The following values are supported and function identically to their CLI counterparts.

If a value is provided on both the command line and via a config file, the values will be merged (if a list like ``exclude_paths``), or the "True" value will be preferred, in the case of something like ``quiet``.

.. code:: yaml

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

.. pre-commit-docs-inclusion-marker-do-not-remove

Pre-commit
==========

To use ansible-lint with pre-commit_, just
add the following to your local repo's ``.pre-commit-config.yaml`` file.
Make sure to change ``sha:`` to be either a git commit sha or tag of
ansible-lint containing ``hooks.yaml``.

.. code:: yaml

    - repo: https://github.com/ansible/ansible-lint.git
      sha: v3.3.1
      hooks:
        - id: ansible-lint

.. pre-commit-docs-inclusion-marker-end-do-not-remove

Contributing
------------

Please read `Contribution guidelines`_ if you wish to contribute.

Authors
-------

ansible-lint was created by `Will Thames`_ and is now maintained as part of the `Ansible`_ by `Red Hat`_ project.

.. _pre-commit: https://pre-commit.com
.. _Contribution guidelines: https://github.com/ansible/ansible-lint/blob/master/CONTRIBUTING.md
.. _Will Thames: https://github.com/willthames
.. _Ansible: https://ansible.com
.. _Red Hat: https://redhat.com
