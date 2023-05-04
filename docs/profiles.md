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

- [internal-error](rules/internal-error.md)
- [load-failure](rules/load-failure.md)
- [parser-error](rules/parser-error.md)
- [syntax-check](rules/syntax-check.md)

## basic

The `basic` profile prevents common coding issues and enforces standard styles
and formatting. It extends [min](#min) profile.

- [command-instead-of-module](rules/command-instead-of-module.md)
- [command-instead-of-shell](rules/command-instead-of-shell.md)
- [deprecated-bare-vars](rules/deprecated-bare-vars.md)
- [deprecated-local-action](rules/deprecated-local-action.md)
- [deprecated-module](rules/deprecated-module.md)
- [inline-env-var](rules/inline-env-var.md)
- [key-order](rules/key-order.md)
- [literal-compare](rules/literal-compare.md)
- [jinja](rules/jinja.md)
- [no-free-form](https://github.com/ansible/ansible-lint/issues/2117)
- [no-jinja-when](rules/no-jinja-when.md)
- [no-tabs](rules/no-tabs.md)
- [partial-become](rules/partial-become.md)
- [playbook-extension](rules/playbook-extension.md)
- [role-name](rules/role-name.md)
- [schema](rules/schema.md)
- [name](rules/name.md)
- [var-naming](rules/var-naming.md)
- [yaml](rules/yaml.md)

## moderate

The `moderate` profile ensures that content adheres to best practices for making
content easier to read and maintain. It extends [basic](#basic) profile.

- [name[template]](rules/name.md)
- [name[imperative]](https://github.com/ansible/ansible-lint/issues/2170)
- [name[casing]](rules/name.md)
- [spell-var-name](https://github.com/ansible/ansible-lint/issues/2168)

## safety

The `safety` profile avoids module calls that can have non-determinant outcomes
or security concerns. It extends [moderate](#moderate) profile.

- [avoid-implicit](rules/avoid-implicit.md)
- [latest](rules/latest.md)
- [package-latest](rules/package-latest.md)
- [risky-file-permissions](rules/risky-file-permissions.md)
- [risky-octal](rules/risky-octal.md)
- [risky-shell-pipe](rules/risky-shell-pipe.md)

## shared

The `shared` profile ensures that content follows best practices for packaging
and publishing. This profile is intended for content creators who want to make
Ansible playbooks, roles, or collections available from
[galaxy.ansible.com](https://galaxy.ansible.com/),
[automation-hub](https://console.redhat.com/ansible/automation-hub), or a
private instance. It extends [safety](#safety) profile.

- [galaxy](rules/galaxy.md)
- [ignore-errors](rules/ignore-errors.md)
- [layout](https://github.com/ansible/ansible-lint/issues/1900)
- [meta-incorrect](rules/meta-incorrect.md)
- [meta-no-tags](rules/meta-no-tags.md)
- [meta-video-links](rules/meta-video-links.md)
- [meta-version](https://github.com/ansible/ansible-lint/issues/2103)
- [meta-runtime](rules/meta-runtime.md)
- [no-changed-when](rules/no-changed-when.md)
- [no-handler](rules/no-handler.md)
- [no-relative-paths](rules/no-relative-paths.md)
- [max-block-depth](https://github.com/ansible/ansible-lint/issues/2173)
- [max-tasks](https://github.com/ansible/ansible-lint/issues/2172)
- [unsafe-loop](https://github.com/ansible/ansible-lint/issues/2038)

## production

The `production` profile ensures that content meets requirements for inclusion
in
[Ansible Automation Platform (AAP)](https://www.redhat.com/en/technologies/management/ansible)
as validated or certified content. It extends [shared](#shared) profile.

- [avoid-dot-notation](https://github.com/ansible/ansible-lint/issues/2174)
- [sanity](https://github.com/ansible/ansible-lint/issues/2121)
- [fqcn](rules/fqcn.md)
- [import-task-no-when](https://github.com/ansible/ansible-lint/issues/2219)
- [meta-no-dependencies](https://github.com/ansible/ansible-lint/issues/2159)
- [single-entry-point](https://github.com/ansible/ansible-lint/issues/2242)
- [use-loop](https://github.com/ansible/ansible-lint/issues/2204)
