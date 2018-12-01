.. _lint_rules:

*****
Rules
*****

.. contents:: Topics

This topic describes how to use the deault Ansible Lint rules, as well as how to create and use custom rules.

Specifying Rules at Runtime
===========================

By default, ``ansible-lint`` uses the rules found in ``ansible-lint/lib/ansiblelint/rules``. To override this behavior and use a custom set of rules, use the ``-r /path/to/custom-rules`` option to provide a directory path containing the custom rules. For multiple rule sets, pass multiple ``-r`` options.

It's also possilbe to use the default rules, plus custom rules. This can be done by passing the ``-R`` to indicate that the deault rules are to be used, along with one or more ``-r`` options.

Using Tags to Include Rules
```````````````````````````

Each rule has an associated set of one or more tags. To view the list of tags for each available rule, use the ``-T`` option. 

The following shows the available tags in an example set of rules, and the rules associated with each tag:

.. code-block:: bash

    $ ansible-lint -v -T
    
    behaviour ['[ANSIBLE0016]']
    bug ['[ANSIBLE0014]']
    deprecated ['[ANSIBLE0015]', '[ANSIBLE0008]', '[ANSIBLE0018]', '[ANSIBLE0019]']
    formatting ['[ANSIBLE0015]', '[ANSIBLE0002]', '[ANSIBLE0009]']
    idempotency ['[ANSIBLE0012]']
    oddity ['[ANSIBLE0017]']
    readability ['[ANSIBLE0011]']
    repeatability ['[ANSIBLE0004]', '[ANSIBLE0010]', '[ANSIBLE0005]']
    resources ['[ANSIBLE0007]', '[ANSIBLE0006]']
    safety ['[ANSIBLE0013]']

To run just the *idempotency* rules, for example, run the following:

.. code-block:: bash

    $ ansible-lint -t idempotency playbook.yml

Excluding Rules
```````````````

To exclude rules from the available set of rules, use the ``-x SKIP_LIST`` option. For example, the following runs all of the rules except those with the tags *readability* and *safety*:

.. code-block:: bash

    $ ansible-lint -x readability,safety playbook.yml

It's also possible to skip specific rules by passing the rule ID. For example, the following excludes rule *ANSIBLE0011*:

.. code-block:: bash

    $ ansible-lint -x ANSIBLE0011 playbook.yml

False Positives: Muting Ansible Lint Warnings
=============================================

Some rules are a bit of a rule of thumb. Advanced *git*, *yum* or *apt* usage, for example, is typically difficult to achieve through the modules. In this case, you should mark the task so that warnings aren't produced.

There are two mechanisms for this - one works with all tasks, the other works with the command checking modules.

Use the ``warn`` parameter with the *command* or *shell* module.

Use ``skip_ansible_lint`` tag with any task that should be skipped.

It's also a good practice to comment the reasons why a task is being skipped.

Here's an example playbook showing the two techniques for muting Ansible Lint warnings:

.. code-block:: yaml

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

Creating Custom Rules
=====================

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

        id = 'ANSIBLE0001'
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

The task argument to ``matchtask`` contains a number of keys - the critical one is *action*. The value of *task['action']* contains the module being used, and the arguments passed, both as key-value pairs and a list of other arguments (e.g. the command used with shell).

In ansible-lint 2.0.0, *task['action']['args']* was renamed *task['action']['module_arguments']* to avoid a clash when a module actually takes args as a parameter key (e.g. ec2_tag)

In ansible-lint 3.0.0 *task['action']['module']* was renamed *task['action']['__ansible_module__']* to avoid a clash when a module take module as an argument. As a precaution, *task['action']['module_arguments']* was renamed *task['action']['__ansible_arguments__']*.
