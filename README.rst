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

.. image:: https://img.shields.io/travis/com/ansible/ansible-lint/master.svg?label=Linux%20builds%20%40%20Travis%20CI
   :target: https://travis-ci.com/ansible/ansible-lint
   :alt: Travis CI build status

.. image:: https://github.com/ansible/ansible-lint/workflows/%F0%9F%91%B7/badge.svg
   :target: https://github.com/ansible/ansible-lint/actions?query=workflow%3A%F0%9F%91%B7
   :alt: 👷 GitHub Actions CI/CD build status — tests

.. image:: https://github.com/ansible/ansible-lint/workflows/%F0%9F%9A%A8/badge.svg
   :target: https://github.com/ansible/ansible-lint/actions?query=workflow%3A%F0%9F%9A%A8
   :alt: 🚨 GitHub Actions CI/CD build status — linters

.. image:: https://img.shields.io/lgtm/grade/python/g/ansible/ansible-lint.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/ansible/ansible-lint/context:python
   :alt: Language grade: Python

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit


Ansible-lint
============

``ansible-lint`` checks playbooks for practices and behaviour that could
potentially be improved. As a community backed project ansible-lint supports
only the last two major versions of Ansible.

`Visit the Ansible Lint docs site <https://docs.ansible.com/ansible-lint/>`_

Installing
==========

.. installing-docs-inclusion-marker-do-not-remove

Installing on Windows is not supported because we use symlinks inside Python packages.

Using Pip
---------

.. code-block:: bash

    pip install ansible-lint

.. _installing_from_source:

From Source
-----------

**Note**: pip 19.0+ is required for installation. Please consult with the `PyPA User Guide`_
to learn more about managing Pip versions.

.. code-block:: bash

    pip install git+https://github.com/ansible/ansible-lint.git

.. _PyPA User Guide: https://packaging.python.org/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date

.. installing-docs-inclusion-marker-end-do-not-remove

Usage
=====

.. usage-docs-inclusion-marker-do-not-remove

Command Line Options
--------------------

The following is the output from ``ansible-lint --help``, providing an overview of the basic command line options:

.. code-block:: bash

    Usage: ansible-lint [options] [playbook.yml [playbook2 ...]]|roledirectory

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -L                    list all the rules
      -q                    quieter, although not silent output
      -p                    parseable output in the format of pep8
      --parseable-severity  parseable output including severity of rule
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
      -v                    Increase verbosity level
      -x SKIP_LIST          only check rules whose id/tags do not match these
                            values
      --nocolor             disable colored output
      --force-color         Try force colored output (relying on ansible's code)
      --exclude=EXCLUDE_PATHS
                            path to directories or files to skip. This option is
                            repeatable.
      -c /path/to/file      Specify configuration file to use.  Defaults to
                              ".ansible-lint"



Linting Playbooks and Roles
---------------------------

It's important to note that ``ansible-lint`` accepts a list of Ansible playbook files or a list of role directories. Starting from a directory that contains the following, the playbook file, ``playbook.yml``, or one of the role subdirectories, such as ``geerlingguy.apache``, can be passed:

.. code-block:: bash

  playbook.yml
  roles/
      geerlingguy.apache/
          tasks/
          handlers/
          files/
          templates/
          vars/
          defaults/
          meta/
      geerlingguy.elasticsearch/
          tasks/
          handlers/
          files/
          templates/
          vars/
          defaults/
          meta/

The following lints the role ``geerlingguy.apache``:

.. code-block:: bash

    $ ansible-lint geerlingguy.apache

    [305] Use shell only when shell functionality is required
    /Users/chouseknecht/.ansible/roles/geerlingguy.apache/tasks/main.yml:19
    Task/Handler: Get installed version of Apache.

    [502] All tasks should be named
    /Users/chouseknecht/.ansible/roles/geerlingguy.apache/tasks/main.yml:29
    Task/Handler: include_vars apache-22.yml

    [502] All tasks should be named
    /Users/chouseknecht/.ansible/roles/geerlingguy.apache/tasks/main.yml:32
    Task/Handler: include_vars apache-24.yml

Here's the contents of ``playbook.yml``, which references multiples roles:

.. code-block:: yaml

  - name: Lint multiple roles
    hosts: all
    tasks:

    - include_role:
      name: geerlingguy.apache

    - include_role:
      name: geerlingguy.elasticsearch

The following lints ``playbook.yml``, which evaluates both the playbook and the referenced roles:

.. code-block:: bash

    $ ansible-lint playbook.yml

    [305] Use shell only when shell functionality is required
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:19
    Task/Handler: Get installed version of Apache.

    [502] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:29
    Task/Handler: include_vars apache-22.yml

    [502] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:32
    Task/Handler: include_vars apache-24.yml

    [502] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.elasticsearch/tasks/main.yml:17
    Task/Handler: service state=started name=elasticsearch enabled=yes

Since ``ansible-lint`` accepts a list of roles or playbooks, the following works as well, producing the same output as the example above:

.. code-block:: bash

    $ ansible-lint geerlingguy.apache geerlingguy.elasticsearch

    [305] Use shell only when shell functionality is required
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:19
    Task/Handler: Get installed version of Apache.

    [502] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:29
    Task/Handler: include_vars apache-22.yml

    [502] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:32
    Task/Handler: include_vars apache-24.yml

    [502] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.elasticsearch/tasks/main.yml:17
    Task/Handler: service state=started name=elasticsearch enabled=yes

Examples
--------

Included in ``ansible-lint/examples`` are some example playbooks with undesirable features. Running ansible-lint on them works, as demonstrated in the following:

.. code-block:: bash

    $ ansible-lint examples/example.yml

    [301] Commands should not change things if nothing needs doing
    examples/example.yml:9
    Task/Handler: unset variable

    [206] Variables should have spaces before and after: {{ var_name }}
    examples/example.yml:10
        action: command echo {{thisvariable}} is not set in this playbook

    [301] Commands should not change things if nothing needs doing
    examples/example.yml:12
    Task/Handler: trailing whitespace

    [201] Trailing whitespace
    examples/example.yml:13
        action: command echo do nothing

    [401] Git checkouts must contain explicit version
    examples/example.yml:15
    Task/Handler: git check

    [401] Git checkouts must contain explicit version
    examples/example.yml:18
    Task/Handler: git check 2

    [301] Commands should not change things if nothing needs doing
    examples/example.yml:24
    Task/Handler: executing git through command

    [303] git used in place of git module
    examples/example.yml:24
    Task/Handler: executing git through command

    [303] git used in place of git module
    examples/example.yml:27
    Task/Handler: executing git through command

    [401] Git checkouts must contain explicit version
    examples/example.yml:30
    Task/Handler: using git module

    [206] Variables should have spaces before and after: {{ var_name }}
    examples/example.yml:34
        action: debug msg="{{item}}"

    [201] Trailing whitespace
    examples/example.yml:35
        with_items:

    [403] Package installs should not use latest
    examples/example.yml:39
    Task/Handler: yum latest

    [403] Package installs should not use latest
    examples/example.yml:44
    Task/Handler: apt latest

    [101] Deprecated always_run
    examples/example.yml:47
    Task/Handler: always run


If playbooks include other playbooks, or tasks, or handlers or roles, these are also handled:

.. code-block:: bash

    $ ansible-lint examples/include.yml

    [301] Commands should not change things if nothing needs doing
    examples/play.yml:5
    Task/Handler: a bad play

    [303] service used in place of service module
    examples/play.yml:5
    Task/Handler: a bad play

    [401] Git checkouts must contain explicit version
    examples/roles/bobbins/tasks/main.yml:2
    Task/Handler: test tasks

    [701] No 'galaxy_info' found
    examples/roles/hello/meta/main.yml:1
    {'meta/main.yml': {'dependencies': [{'role': 'bobbins', '__line__': 3, '__file__': '/Users/akx/build/ansible-lint/examples/roles/hello/meta/main.yml'}], '__line__': 1, '__file__': '/Users/akx/build/ansible-lint/examples/roles/hello/meta/main.yml', 'skipped_rules': []}}

    [303] service used in place of service module
    examples/roles/morecomplex/handlers/main.yml:1
    Task/Handler: restart service using command

    [301] Commands should not change things if nothing needs doing
    examples/roles/morecomplex/tasks/main.yml:1
    Task/Handler: test bad command

    [302] mkdir used in place of argument state=directory to file module
    examples/roles/morecomplex/tasks/main.yml:1
    Task/Handler: test bad command

    [301] Commands should not change things if nothing needs doing
    examples/roles/morecomplex/tasks/main.yml:4
    Task/Handler: test bad command v2

    [302] mkdir used in place of argument state=directory to file module
    examples/roles/morecomplex/tasks/main.yml:4
    Task/Handler: test bad command v2

    [301] Commands should not change things if nothing needs doing
    examples/roles/morecomplex/tasks/main.yml:7
    Task/Handler: test bad local command

    [305] Use shell only when shell functionality is required
    examples/roles/morecomplex/tasks/main.yml:7
    Task/Handler: test bad local command

    [504] Do not use 'local_action', use 'delegate_to: localhost'
    examples/roles/morecomplex/tasks/main.yml:8
      local_action: shell touch foo

    [201] Trailing whitespace
    examples/tasks/x.yml:3
      args:

    [201] Trailing whitespace
    examples/tasks/x.yml:3
      args:

.. usage-docs-inclusion-marker-end-do-not-remove

Configuring
===========

.. configuring-docs-inclusion-marker-do-not-remove

Configuration File
------------------

Ansible-lint supports local configuration via a ``.ansible-lint`` configuration file. Ansible-lint checks the working directory for the presence of this file and applies any configuration found there. The configuration file location can also be overridden via the ``-c path/to/file`` CLI flag.

If a value is provided on both the command line and via a config file, the values will be merged (if a list like **exclude_paths**), or the **True** value will be preferred, in the case of something like **quiet**.

The following values are supported, and function identically to their CLI counterparts:

.. code-block:: yaml

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


Pre-commit Setup
----------------

To use ansible-lint with `pre-commit`_, just add the following to your local repo's ``.pre-commit-config.yaml`` file. Make sure to change **rev:** to be either a git commit sha or tag of ansible-lint containing ``hooks.yaml``.

.. code-block:: yaml

    - repo: https://github.com/ansible/ansible-lint.git
      rev: v4.1.0
      hooks:
        - id: ansible-lint
          files: \.(yaml|yml)$

.. _pre-commit: https://pre-commit.com

.. configuring-docs-inclusion-marker-end-do-not-remove

Rules
=====

.. rules-docs-inclusion-marker-do-not-remove

Specifying Rules at Runtime
---------------------------

By default, ``ansible-lint`` uses the rules found in ``ansible-lint/lib/ansiblelint/rules``. To override this behavior and use a custom set of rules, use the ``-r /path/to/custom-rules`` option to provide a directory path containing the custom rules. For multiple rule sets, pass multiple ``-r`` options.

It's also possilbe to use the default rules, plus custom rules. This can be done by passing the ``-R`` to indicate that the deault rules are to be used, along with one or more ``-r`` options.

Using Tags to Include Rules
```````````````````````````

Each rule has an associated set of one or more tags. To view the list of tags for each available rule, use the ``-T`` option.

The following shows the available tags in an example set of rules, and the rules associated with each tag:

.. code-block:: bash

    $ ansible-lint -v -T

    behaviour ['[503]']
    bug ['[304]']
    command-shell ['[305]', '[302]', '[304]', '[306]', '[301]', '[303]']
    deprecated ['[105]', '[104]', '[103]', '[101]', '[102]']
    formatting ['[104]', '[203]', '[201]', '[204]', '[206]', '[205]', '[202]']
    idempotency ['[301]']
    idiom ['[601]', '[602]']
    metadata ['[701]', '[704]', '[703]', '[702]']
    module ['[404]', '[401]', '[403]', '[402]']
    oddity ['[501]']
    readability ['[502]']
    repeatability ['[401]', '[403]', '[402]']
    resources ['[302]', '[303]']
    safety ['[305]']
    task ['[502]', '[503]', '[504]', '[501]']

To run just the *idempotency* rules, for example, run the following:

.. code-block:: bash

    $ ansible-lint -t idempotency playbook.yml

Excluding Rules
```````````````

To exclude rules from the available set of rules, use the ``-x SKIP_LIST`` option. For example, the following runs all of the rules except those with the tags *readability* and *safety*:

.. code-block:: bash

    $ ansible-lint -x readability,safety playbook.yml

It's also possible to skip specific rules by passing the rule ID. For example, the following excludes rule *502*:

.. code-block:: bash

    $ ansible-lint -x 502 playbook.yml

False Positives: Skipping Rules
-------------------------------

Some rules are a bit of a rule of thumb. Advanced *git*, *yum* or *apt* usage, for example, is typically difficult to achieve through the modules. In this case, you should mark the task so that warnings aren't produced.

To skip a specific rule for a specific task, inside your ansible yaml add ``# noqa [rule_id]`` at the end of the line. If the rule is task-based (most are), add at the end of any line in the task. You can skip multiple rules via a space-separated list.

.. code-block:: yaml

    - name: this would typically fire GitHasVersionRule 401 and BecomeUserWithoutBecomeRule 501
      become_user: alice  # noqa 401 501
      git: src=/path/to/git/repo dest=checkout

If the rule is line-based, ``# noqa [rule_id]`` must be at the end of the particular line to be skipped

.. code-block:: yaml

    - name: this would typically fire LineTooLongRule 204 and VariableHasSpacesRule 206
      get_url:
        url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf  # noqa 204
        dest: "{{dest_proj_path}}/foo.conf"  # noqa 206


It's also a good practice to comment the reasons why a task is being skipped.

If you want skip running a rule entirely, you can use either:

* `command-line skip_list`_ via ``-x``
* `config file skip_list`_

A less-preferred method of skipping is to skip all task-based rules for a task (this does not skip line-based rules). There are two mechanisms for this: the ``skip_ansible_lint`` tag works with all tasks, and the ``warn`` parameter works with the *command* or *shell* modules only. Examples:

.. code-block:: yaml

    - name: this would typically fire CommandsInsteadOfArgumentRule 302
      command: warn=no chmod 644 X

    - name: this would typically fire CommandsInsteadOfModuleRule 303
      command: git pull --rebase
      args:
        warn: False

    - name: this would typically fire GitHasVersionRule 401
      git: src=/path/to/git/repo dest=checkout
      tags:
      - skip_ansible_lint

Creating Custom Rules
---------------------

Rules are described using a class file per rule. Default rules are named *DeprecatedVariableRule.py*, etc.

Each rule definition should have the following:

* ID: A unique identifier
* Short description: Brief description of the rule
* Description: Behaviour the rule is looking for
* Tags: one or more tags that may be used to include or exclude the rule
* At least one of the following methods:

  * ``match`` that takes a line and returns None or False, if the line doesn't match the test, and True or a custom message, when it does. (This allows one rule to test multiple behaviours - see e.g. the *CommandsInsteadOfModulesRule*.)
  * ``matchtask`` that operates on a single task or handler, such that tasks get standardized to always contain a *module* key and *module_arguments* key. Other common task modifiers, such as *when*, *with_items*, etc., are also available as keys, if present in the task.

An example rule using ``match`` is:

.. code-block:: python

    from ansiblelint import AnsibleLintRule

    class DeprecatedVariableRule(AnsibleLintRule):

        id = 'EXAMPLE002'
        shortdesc = 'Deprecated variable declarations'
        description = 'Check for lines that have old style ${var} ' + \
                      'declarations'
        tags = { 'deprecated' }

        def match(self, file, line):
            return '${' in line

An example rule using ``matchtask`` is:

.. code-block:: python

    import ansiblelint.utils
    from ansiblelint import AnsibleLintRule

    class TaskHasTag(AnsibleLintRule):
        id = 'EXAMPLE001'
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

The task argument to ``matchtask`` contains a number of keys - the critical one is *action*. The value of *task['action']* contains the module being used, and the arguments passed, both as key-value pairs and a list of other arguments (e.g. the command used with shell).

In ansible-lint 2.0.0, *task['action']['args']* was renamed *task['action']['module_arguments']* to avoid a clash when a module actually takes args as a parameter key (e.g. ec2_tag)

In ansible-lint 3.0.0 *task['action']['module']* was renamed *task['action']['__ansible_module__']* to avoid a clash when a module take module as an argument. As a precaution, *task['action']['module_arguments']* was renamed *task['action']['__ansible_arguments__']*.

.. rules-docs-inclusion-marker-end-do-not-remove

Contributing
============

Please read `Contribution guidelines`_ if you wish to contribute.

Authors
=======

ansible-lint was created by `Will Thames`_ and is now maintained as part of the `Ansible`_ by `Red Hat`_ project.

.. _Contribution guidelines: https://github.com/ansible/ansible-lint/blob/master/CONTRIBUTING.md
.. _Will Thames: https://github.com/willthames
.. _Ansible: https://ansible.com
.. _Red Hat: https://redhat.com
.. _command-line skip_list: https://docs.ansible.com/ansible-lint/usage/usage.html#command-line-options
.. _config file skip_list: https://docs.ansible.com/ansible-lint/configuring/configuring.html#configuration-file
