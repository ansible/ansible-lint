4.0.1 - Released 04-Jan-2019
============================

Bugfix release

- Allow install with python35 and add to tox testing `#452 <https://github.com/ansible/ansible-lint/pull/452>`_
- Fix 503 UseHandlerRatherThanWhenChangedRule attempt to iterate on bool `#455 <https://github.com/ansible/ansible-lint/pull/455>`_
- Improve regex on rule 602 `#454 <https://github.com/ansible/ansible-lint/pull/454>`_
- Refactor RoleRelativePathRule, fix keyerror `#446 <https://github.com/ansible/ansible-lint/pull/446>`_
- Rule 405 now ignore case of 'yum: list=package' `#444 <https://github.com/ansible/ansible-lint/pull/444>`_
- Allow jinja escaping in variables `#440 <https://github.com/ansible/ansible-lint/pull/440>`_

4.0.0 - Released 18-Dec-2018
============================

* New documentation site `docs.ansible.com/ansible-lint <https://docs.ansible.com/ansible-lint/>`_
* Additional default rules for ansible-lint, listed in `docsite default rules <https://docs.ansible.com/ansible-lint/rules/default_rules.html>`_
* Fixed running with role path containing single or multiple dirs #390
* Fixed double sudo rule output #393
* Severity property added to rules to be used by Galaxy #379
* Packaging: consistency and automation #389
* Updated rule TrailingWhitespaceRule.py to remove carriage return char #323
* Allow snake_case module names for rules #82
* Suggest tempfile module instead of mktemp command #422
* Update tox to run with only supported ansible versions #406
* GitHub repository edits: move to ansible org, add CODE_OF_CONDUCT, add ROADMAP, label edits

3.5.1
=====

Use ``yaml.safe_load`` for loading the configuration file

3.5.0
=====

* New ids and tags, add doc generator. Old tag names remain backwardly compatible (awcrosby)
* Add more package formats to PackageIsNotLatestRule (simon04)
* Improve handling of meta/main.yml dependencies (MatrixCrawler)
* Correctly handle role argument trailing slash (zoredache)
* Handle ``include_task`` and ``import_task`` (zeot)
* Add a new rule to detect jinja in when clauses (greg-hellings)
* Suggest ``replace`` as another alternative to ``sed`` (inponomarev)
* YAML syntax highlighting for false positives (gundalow)

3.4.23
======

Fix bug with using comma-separated ``skip_list`` arguments

3.4.22
======

* Allow ``include_role`` and ``import_role`` (willthames)
* Support arbitrary number of exclude flags (KellerFuchs)
* Fix task has name check for empty name fields (ekeih)
* Allow vault encrypted variables in YAML files (mozz)
* Octal permission check improvements - readability, test
  coverage and bug fixes (willthames)
* Fix very weird bug with line numbers in some test environments (kouk)
* Python 3 fixes for octal literals in tests (willthames)
