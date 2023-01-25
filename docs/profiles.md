<!---
Do not manually edit, generated from generate_docs.py
-->

# Profiles

Ansible-lint profiles gradually increase the strictness of rules as your Ansible
content lifecycle. To configure linter to use a specific profile, read
[applying-profiles][].

!!! note

    Rules with `*` in the suffix are not yet implemented but are documented with linked GitHub issues.

## min

The `min` profile ensures that Ansible can load content. Rules in this profile
are mandatory because they prevent fatal errors. You can add files to the
exclude list or provide dependencies to load the correct files.

- [internal-error](rules/internal-error/)
- [load-failure](rules/load-failure/)
- [parser-error](rules/parser-error/)
- [syntax-check](rules/syntax-check/)

## basic

The `basic` profile prevents common coding issues and enforces standard styles
and formatting. It extends [min](#min) profile.

- [command-instead-of-module](rules/command-instead-of-module/)
- [command-instead-of-shell](rules/command-instead-of-shell/)
- [deprecated-bare-vars](rules/deprecated-bare-vars/)
- [deprecated-command-syntax](rules/deprecated-command-syntax/)
- [deprecated-local-action](rules/deprecated-local-action/)
- [deprecated-module](rules/deprecated-module/)
- [inline-env-var](rules/inline-env-var/)
- [key-order](rules/key-order/)
- [literal-compare](rules/literal-compare/)
- [jinja](rules/jinja/)
- [no-jinja-when](rules/no-jinja-when/)
- [no-tabs](rules/no-tabs/)
- [partial-become](rules/partial-become/)
- [playbook-extension](rules/playbook-extension/)
- [role-name](rules/role-name/)
- [schema](rules/schema/)
- [name](rules/name/)
- [var-naming](rules/var-naming/)
- [yaml](rules/yaml/)

## moderate

The `moderate` profile ensures that content adheres to best practices for making
content easier to read and maintain. It extends [basic](#basic) profile.

- [name[template]](rules/name/)
- [name[imperative]](https://github.com/ansible/ansible-lint/issues/2170)
- [name[casing]](rules/name/)
- [no-free-form](https://github.com/ansible/ansible-lint/issues/2117)
- [spell-var-name](https://github.com/ansible/ansible-lint/issues/2168)

## safety

The `safety` profile avoids module calls that can have non-determinant outcomes
or security concerns. It extends [moderate](#moderate) profile.

- [avoid-implicit](rules/avoid-implicit/)
- [latest](rules/latest/)
- [package-latest](rules/package-latest/)
- [risky-file-permissions](rules/risky-file-permissions/)
- [risky-octal](rules/risky-octal/)
- [risky-shell-pipe](rules/risky-shell-pipe/)

## shared

The `shared` profile ensures that content follows best practices for packaging
and publishing. This profile is intended for content creators who want to make
Ansible playbooks, roles, or collections available from
[galaxy.ansible.com](https://galaxy.ansible.com),
[automation-hub](https://console.redhat.com/ansible/automation-hub), or a
private instance. It extends [safety](#safety) profile.

- [galaxy](rules/galaxy/)
- [ignore-errors](rules/ignore-errors/)
- [layout](https://github.com/ansible/ansible-lint/issues/1900)
- [meta-incorrect](rules/meta-incorrect/)
- [meta-no-info](rules/meta-no-info/)
- [meta-no-tags](rules/meta-no-tags/)
- [meta-video-links](rules/meta-video-links/)
- [meta-version](https://github.com/ansible/ansible-lint/issues/2103)
- [meta-unsupported-ansible](https://github.com/ansible/ansible-lint/issues/2102)
- [no-changed-when](rules/no-changed-when/)
- [no-changelog](https://github.com/ansible/ansible-lint/issues/2101)
- [no-handler](rules/no-handler/)
- [no-relative-paths](rules/no-relative-paths/)
- [max-block-depth](https://github.com/ansible/ansible-lint/issues/2173)
- [max-tasks](https://github.com/ansible/ansible-lint/issues/2172)
- [unsafe-loop](https://github.com/ansible/ansible-lint/issues/2038)

## production

The `production` profile ensures that content meets requirements for inclusion
in
[Ansible Automation Platform (AAP)](https://www.redhat.com/en/technologies/management/ansible)
as validated or certified content. It extends [shared](#shared) profile.

- [avoid-dot-notation](https://github.com/ansible/ansible-lint/issues/2174)
- [disallowed-ignore](https://github.com/ansible/ansible-lint/issues/2121)
- [fqcn](rules/fqcn/)
- [import-task-no-when](https://github.com/ansible/ansible-lint/issues/2219)
- [meta-no-dependencies](https://github.com/ansible/ansible-lint/issues/2159)
- [single-entry-point](https://github.com/ansible/ansible-lint/issues/2242)
- [use-loop](https://github.com/ansible/ansible-lint/issues/2204)
