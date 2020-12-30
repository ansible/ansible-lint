Current changes can now be accessed from `github releases <https://github.com/ansible-community/ansible-lint/releases/>`_.

4.3.0 - Released 2020-08-17
===========================

Major Changes:

* Require Python 3.6 or newer (#775) @ssbarnea
* Require Ansible 2.8 or newer (#721) @ssbarnea
* LRU Cache for frequently called functions (#891) @ragne
* Change documentation website to RTD (#875) @ssbarnea
* Add rules for verifying the existence of imported and included files (#691)
  @jlusiardi
* Add a new rule for detecting nested jinja mustache syntax (#686) @europ

Minor Changes:

* Refactored import_playbook tests (#951) @ssbarnea
* Added MissingFilePermissionsRule (#943) @ssbarnea
* Enable github actions parsable format (#926) @ssbarnea
* Add linter branding for docs (#914) @ssbarnea
* Assure we do not produce duplicated matches (#912) @ssbarnea
* Enable annotations on failed tests (#910) @ssbarnea
* Refactor `_taskshandlers_children` complexity (#903) @webknjaz
* Make import sections consistent (#897) @ssbarnea
* Allow backticks in shell commands (#894) @turettn
* Add ansible210 testing (#888) @ssbarnea
* Enable isort (#887) @ssbarnea
* Combine MatchError into Match (#884) @ssbarnea
* Improve MatchError class (#881) @ssbarnea
* Expose package version (#867) @ssbarnea
* Replace custom theme with sphinx-ansible-theme (#856) @ssbarnea
* Improve unjinja function (#853) @ssbarnea
* Refactor MetaMainHasInfoRule (#846) @ssato
* Remove dependency on ansible.utils.color (#833) @ssbarnea
* Moved exit codes to constants (#821) @ssbarnea
* Document module dependencies (#817) @ssbarnea
* Refactor Runner out of __init__ (#816) @ssbarnea
* Added reproducer for become in blocks (#793) @ssbarnea
* Convert failed to find required 'name' key in include_role into a match
  (#781) @ssbarnea
* Fix exclude_paths from get_playbooks_and_roles (#774) @ssbarnea
* Update ComparisonToEmptyStringRule.py (#770) @vbotka
* Remove bin/ansible-lint script (#762) @ssbarnea
* Fix logging configuration (#757) @ssbarnea
* Allow returning line number in matchplay (#756) @albinvass
* Update cli output on README (#754) @ssbarnea
* Migrate some test to pytest (#740) @cans
* Use python logging (#732) @ssbarnea
* Make config loading failures visible (#726) @ssbarnea
* Add a test that fails with `AttributeError` on malformed `import_tasks` file
  content (#720) @mdaniel
* Consistent relative path display (#692) @cans

Bugfixes:

* E501: Add become_user and become inheritance (#964) @Tompage1994
* Add missing hosts to test files (#952) @ssbarnea
* E208: Improve MissingFilePermissionsRule detection (#949) @ssbarnea
* Make pre-commit hook use auto-detect mode (#932) @ssbarnea
* Fix severity formatter wrong use of color (#919) @ssbarnea
* Avoid displaying Null with missing filenames (#918) @ssbarnea
* Include contributing inside docs (#905) @ssbarnea
* Fix spelling mistakes in documentation (#901) @MorganGeek
* Avoid failure with playbooks having tasks key a null value (#899) @ssbarnea
* Fix `MatchError` comparison fallback implementation (#896) @webknjaz
* Avoid sorting failure with matches without an id (#879) @ssbarnea
* Fix broken always_run rule on Ansible 2.10 (#878) @ssbarnea
* Allow null config file (#814) @ssbarnea
* Fixed the search method when the file path not exists (#807) @cahlchang
* Restore playbook auto-detection (#767) @ssbarnea
* Gracefully process a missing git binary when falling-back to pure-python
  discovery (#738) @anryko
* Resurrect support for editable mode installs (#722) @webknjaz
* Avoid exception from 505 rule (#709) @ssbarnea

4.2.0 - Released 2019-12-04
===========================

Features:

- Enable ansible-lint to auto-detect roles/playbooks `#615 <https://github.com/ansible-community/ansible-lint/pull/615>`_
- Normalize displayed file paths `#620 <https://github.com/ansible-community/ansible-lint/pull/620>`_

Bugfixes:

- Fix role detection to include tasks/main.yml `#631 <https://github.com/ansible-community/ansible-lint/pull/631>`_
- Fix pre-commit hooks `#612 <https://github.com/ansible-community/ansible-lint/pull/612>`_
- Ensure variable syntax before matching in VariableHasSpacesRule `#535 <https://github.com/ansible-community/ansible-lint/pull/535>`_
- Fix false positive with multiline template in UsingBareVariablesIsDeprecatedRule `#251 <https://github.com/ansible-community/ansible-lint/pull/251>`_
- Fix role metadata checks when they include unexpected types `#533 <https://github.com/ansible-community/ansible-lint/pull/533>`_ `#513 <https://github.com/ansible-community/ansible-lint/pull/513>`_
- Support inline rule skipping inside a block `#528 <https://github.com/ansible-community/ansible-lint/pull/528>`_
- Look for noqa skips in handlers, pre_tasks, and post_tasks `#520 <https://github.com/ansible-community/ansible-lint/pull/520>`_
- Fix skipping when using import_playbook `#517 <https://github.com/ansible-community/ansible-lint/pull/517>`_
- Fix parsing inline args for import_role and include_role `#511 <https://github.com/ansible-community/ansible-lint/pull/511>`_
- Fix syntax proposed by 104 to not fail 206 `#501 <https://github.com/ansible-community/ansible-lint/pull/501>`_
- Fix VariableHasSpacesRule false positive for whitespace control chars in vars `#500 <https://github.com/ansible-community/ansible-lint/pull/500>`_

Docs/Misc:

- Disable docs build on macos with py38 `#630 <https://github.com/ansible-community/ansible-lint/pull/630>`_
- Update dependencies and CI to supported versions of ansible `#530 <https://github.com/ansible-community/ansible-lint/pull/530>`_
- Declare support for Python 3.8 `#601 <https://github.com/ansible-community/ansible-lint/pull/601>`_

Dev/Contributor:

- Enable flake-docstrings to check for pep257 `#621 <https://github.com/ansible-community/ansible-lint/pull/621>`_
- Remove code related to unsupported ansible versions before 2.4 `#622 <https://github.com/ansible-community/ansible-lint/pull/622>`_
- Replace nosetests with pytest `#604 <https://github.com/ansible-community/ansible-lint/pull/604>`_
- Support newer setuptools and require 34.0.0 or later `#591 <https://github.com/ansible-community/ansible-lint/pull/591>`_ `#600 <https://github.com/ansible-community/ansible-lint/pull/600>`_
- Added SSL proxy variables to tox passenv `#593 <https://github.com/ansible-community/ansible-lint/pull/593>`_
- Have RunFromText test helper use named files for playbooks `#519 <https://github.com/ansible-community/ansible-lint/pull/519>`_
- Fully depend on Pip having PEP 517 implementation `#607 <https://github.com/ansible-community/ansible-lint/pull/607>`_
- Fixed metadata and travis deployment `#598 <https://github.com/ansible-community/ansible-lint/pull/598>`_

4.1.0 - Released 11-Feb-2019
============================

- Support skipping specific rule(s) for a specific task `#460 <https://github.com/ansible-community/ansible-lint/pull/460>`_
- Lint all yaml in tasks/ and handlers/ regardless of import or include `#462 <https://github.com/ansible-community/ansible-lint/pull/462>`_
- New rule: shell task uses pipeline without pipefail `#199 <https://github.com/ansible-community/ansible-lint/pull/199>`_
- Remove rule 405 checking for retry on package modules `#465 <https://github.com/ansible-community/ansible-lint/pull/465>`_
- Limit env var check to command, not shell `#477 <https://github.com/ansible-community/ansible-lint/pull/477>`_
- Extend max line length rule from 120 to 160 `#474 <https://github.com/ansible-community/ansible-lint/pull/474>`_
- Do not flag octal file mode permission when it is a string `#480 <https://github.com/ansible-community/ansible-lint/pull/480>`_
- Check ANSIBLE_ROLES_PATH before basedir `#478 <https://github.com/ansible-community/ansible-lint/pull/478>`_
- Fix crash on indexing empty cmd arguments `#473 <https://github.com/ansible-community/ansible-lint/pull/473>`_
- Handle argv syntax for the command module `#424 <https://github.com/ansible-community/ansible-lint/pull/424>`_
- Add another possible license default with SPDX `#472 <https://github.com/ansible-community/ansible-lint/pull/472>`_
- Ignore comments for line-based rules `#453 <https://github.com/ansible-community/ansible-lint/pull/453>`_
- Allow config skip_list to have rule number id not in quotes `#463 <https://github.com/ansible-community/ansible-lint/pull/463>`_

4.0.1 - Released 04-Jan-2019
============================

Bugfix release

- Allow install with python35 and add to tox testing `#452 <https://github.com/ansible-community/ansible-lint/pull/452>`_
- Fix 503 UseHandlerRatherThanWhenChangedRule attempt to iterate on bool `#455 <https://github.com/ansible-community/ansible-lint/pull/455>`_
- Improve regex on rule 602 `#454 <https://github.com/ansible-community/ansible-lint/pull/454>`_
- Refactor RoleRelativePathRule, fix keyerror `#446 <https://github.com/ansible-community/ansible-lint/pull/446>`_
- Rule 405 now ignore case of 'yum: list=package' `#444 <https://github.com/ansible-community/ansible-lint/pull/444>`_
- Allow jinja escaping in variables `#440 <https://github.com/ansible-community/ansible-lint/pull/440>`_

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
* GitHub repository edits: move to ansible org, add CODE_OF_CONDUCT, add
  ROADMAP, label edits

3.5.1
=====

Use ``yaml.safe_load`` for loading the configuration file

3.5.0
=====

* New ids and tags, add doc generator. Old tag names remain backwardly\
  compatible (awcrosby)
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
