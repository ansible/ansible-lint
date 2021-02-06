.. _lint_documentation:

Ansible Lint Documentation
==========================

About Ansible Lint
``````````````````

Ansible Lint is a command-line tool for linting **playbooks, roles and
collections** aimed towards any Ansible users. Its main goal is to promote
proven practices, patterns and behaviors while avoiding common pitfals that can
easily lead to bugs or make code harder to maintain.

Ansible lint is also supposed to help users upgrade their code to work with
newer versions of Ansible. Due to this reason we recommend using it with
the newest version of Ansible, even if the version used in production may be
older.

As any other linter, it is opinionated. Still, its rules are the result of
community contributions and they can always be disabled based individually or
by category by each user.

`Ansible Galaxy project <https://github.com/ansible/galaxy/>`_ makes use of
this linter in order to compute quality scores for `Galaxy Hub <https://galaxy.ansible.com>`_
contributed content. This does not mean this tool is aimed only to those
that want to share their code. Files like ``galaxy.yml``, or sections like
``galaxy_info`` inside ``meta.yml`` help with documentation and maintenance,
even for unpublished roles or collections.

The project was originally started by `@willthames <https://github.com/willthames/>`_,
and has since been adopted by the Ansible Community team. Its development is
purely community driven, while keeping permanent communications with other
Ansible teams.

.. toctree::
   :maxdepth: 3
   :caption: Installing

   installing

.. toctree::
   :maxdepth: 3
   :caption: Usage

   usage

.. toctree::
   :maxdepth: 3
   :caption: Configuring

   configuring

.. toctree::
   :maxdepth: 4
   :caption: Rules

   rules
   custom-rules
   default_rules

.. toctree::
   :caption: Contributing

   contributing
