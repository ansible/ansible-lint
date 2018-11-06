
.. _using_lint:


*****
Usage
*****

.. contents:: Topics

This topic describes how to use ``ansible-lint``.


Command Line Options
====================

The following is the output from ``ansible-lint --help``, providing an overview of the basic command line options:

.. code-block:: bash

    Usage: ansible-lint [options] playbook.yml [playbook2 ...]
    
    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -L                    list all the rules
      -q                    quieter, although not silent output
      -p                    parseable output in the format of pep8
      -r RULESDIR           specify one or more rules directories using one or
                            more -r arguments. Any -r flags override the default
                            rules in ~/ansible-lint/lib/ansiblelint/rules, unless -R is also used.
      -R                    Use default rules in ~/ansible-lint/lib/ansiblelint/rules in addition to any
                            extra rules directories specified with -r. There is no
                            need to specify this if no -r flags are used
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
      -c C                  Specify configuration file to use.  Defaults to
                            ".ansible-lint"



Linting Playbooks and Roles
===========================

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
    
    [ANSIBLE0013] Use shell only when shell functionality is required
    /Users/chouseknecht/.ansible/roles/geerlingguy.apache/tasks/main.yml:19
    Task/Handler: Get installed version of Apache.
    
    [ANSIBLE0011] All tasks should be named
    /Users/chouseknecht/.ansible/roles/geerlingguy.apache/tasks/main.yml:29
    Task/Handler: include_vars apache-22.yml
    
    [ANSIBLE0011] All tasks should be named
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

    [ANSIBLE0013] Use shell only when shell functionality is required
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:19
    Task/Handler: Get installed version of Apache.
    
    [ANSIBLE0011] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:29
    Task/Handler: include_vars apache-22.yml
    
    [ANSIBLE0011] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:32
    Task/Handler: include_vars apache-24.yml
    
    [ANSIBLE0011] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.elasticsearch/tasks/main.yml:17
    Task/Handler: service state=started name=elasticsearch enabled=yes

Since ``ansible-lint`` accepts a list of roles or playbooks, the following works as well, producing the same output as the example above:

.. code-block:: bash

    $ ansible-lint geerlingguy.apache geerlingguy.elasticsearch

    [ANSIBLE0013] Use shell only when shell functionality is required
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:19
    Task/Handler: Get installed version of Apache.
    
    [ANSIBLE0011] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:29
    Task/Handler: include_vars apache-22.yml
    
    [ANSIBLE0011] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.apache/tasks/main.yml:32
    Task/Handler: include_vars apache-24.yml
    
    [ANSIBLE0011] All tasks should be named
    /Users/chouseknecht/roles/geerlingguy.elasticsearch/tasks/main.yml:17
    Task/Handler: service state=started name=elasticsearch enabled=yes

Examples
========

Included in ``ansible-lint/examples`` are some example playbooks with undesirable features. Running ansible-lint on them works, as demonstrated in the following:

.. code-block:: bash

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
    If playbooks include other playbooks, or tasks, or handlers or roles, these are also handled:

.. code-block:: bash

    $ bin/ansible-lint examples/include.yml

    [ANSIBLE0004] Checkouts must contain explicit version
    /Users/will/src/ansible-lint/examples/roles/bobbins/tasks/main.yml:3
    action: git a=b c=d
