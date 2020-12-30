.. _lint_rules:

*****
Rules
*****

Specifying Rules at Runtime
---------------------------

By default, ``ansible-lint`` uses the rules found in
``ansible-lint/lib/ansiblelint/rules``. To override this behavior and use a
custom set of rules, use the ``-r /path/to/custom-rules`` option to provide a
directory path containing the custom rules. For multiple rule sets, pass
multiple ``-r`` options.

It's also possible to use the default rules, plus custom rules. This can be
done by passing the ``-R`` to indicate that the default rules are to be used,
along with one or more ``-r`` options.

Using Tags to Include Rules
```````````````````````````

Each rule has an associated set of one or more tags. To view the list of tags
for each available rule, use the ``-T`` option.

The following shows the available tags in an example set of rules, and the
rules associated with each tag:

.. code-block:: console

    $ ansible-lint -v -T

    behaviour ['[503]']
    bug ['[304]']
    command-shell ['[305]', '[302]', '[304]', '[306]', '[301]', '[303]']
    deprecations ['[105]', '[104]', '[103]', '[101]', '[102]']
    experimental ['[208]']
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

To exclude rules from the available set of rules, use the ``-x SKIP_LIST``
option. For example, the following runs all of the rules except those with the
tags *readability* and *safety*:

.. code-block:: bash

    $ ansible-lint -x readability,safety playbook.yml

It's also possible to skip specific rules by passing the rule ID. For example,
the following excludes rule *502*:

.. code-block:: bash

    $ ansible-lint -x 502 playbook.yml

Ignoring Rules
``````````````

To only warn about rules, use the ``-w WARN_LIST`` option. In this example all
rules are run, but if rules with the ``experimental`` tag match they only show
an error message but don't change the exit code:

.. code-block:: console

    $ ansible-lint -w experimental playbook.yml

The default value for ``WARN_LIST`` is ``['experimental']`` if you don't
define your own either on the cli or in the config file. If you do define your
own ``WARN_LIST`` you will need to add ``'experimental'`` to it if you don't
want experimental rules to change your exit code.

False Positives: Skipping Rules
-------------------------------

Some rules are a bit of a rule of thumb. Advanced *git*, *yum* or *apt* usage,
for example, is typically difficult to achieve through the modules. In this
case, you should mark the task so that warnings aren't produced.

To skip a specific rule for a specific task, inside your ansible yaml add
``# noqa [rule_id]`` at the end of the line. If the rule is task-based (most
are), add at the end of any line in the task. You can skip multiple rules via
a space-separated list.

.. code-block:: yaml

    - name: this would typically fire GitHasVersionRule 401 and BecomeUserWithoutBecomeRule 501
      become_user: alice  # noqa 401 501
      git: src=/path/to/git/repo dest=checkout

If the rule is line-based, ``# noqa [rule_id]`` must be at the end of the
particular line to be skipped

.. code-block:: yaml

    - name: this would typically fire LineTooLongRule 204 and VariableHasSpacesRule 206
      get_url:
        url: http://example.com/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/really_long_path/file.conf  # noqa 204
        dest: "{{dest_proj_path}}/foo.conf"  # noqa 206


It's also a good practice to comment the reasons why a task is being skipped.

If you want skip running a rule entirely, you can use either use ``-x`` command
line argument, or add it to ``skip_list`` inside the configuration file.

A less-preferred method of skipping is to skip all task-based rules for a task
(this does not skip line-based rules). There are two mechanisms for this: the
``skip_ansible_lint`` tag works with all tasks, and the ``warn`` parameter
works with the *command* or *shell* modules only. Examples:

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
