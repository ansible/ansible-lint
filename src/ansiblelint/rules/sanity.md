# sanity

This rule checks the `tests/sanity/ignore-x.x.txt` file for disallowed ignores.
This rule is extremely opinionated and enforced by Partner Engineering as a requirement for Red Hat Certification. The
currently allowed ruleset is subject to change, but is starting at a minimal
number of allowed ignores for maximum test enforcement. Any commented-out ignore
entries are not evaluated, and ignore files for unsupported versions of ansible-core are not evaluated.

This rule can produce messages like:

- `sanity[cannot-ignore]` - Ignore file contains {test} at line {line_num},
  which is not a permitted ignore.
- `sanity[bad-ignore]` - Ignore file entry at {line_num} is formatted
  incorrectly. Please review.

Currently allowed ignores for all Ansible versions are:

- `validate-modules:missing-gplv3-license`
- `action-plugin-docs`
- `import-2.6`
- `import-2.6!skip`
- `import-2.7`
- `import-2.7!skip`
- `import-3.5`
- `import-3.5!skip`
- `compile-2.6`
- `compile-2.6!skip`
- `compile-2.7`
- `compile-2.7!skip`
- `compile-3.5`
- `compile-3.5!skip`
- `shellcheck`
- `shebang`
- `pylint:used-before-assignment`

## Problematic code

```
# tests/sanity/ignore-x.x.txt
plugins/module_utils/ansible_example_module.py import-3.6!skip
```

```
# tests/sanity/ignore-x.x.txt
plugins/module_utils/ansible_example_module.oops-3.6!skip
```

## Correct code

```
# tests/sanity/ignore-x.x.txt
plugins/module_utils/ansible_example_module.py import-2.7!skip
```
