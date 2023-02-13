# latest

The `latest` rule checks that module arguments like those used for source
control checkout do not have arguments that might generate different results
based on context.

This more generic rule replaced two older rules named `git-latest` and
`hg-latest`.

We are aware that there are genuine cases where getting the tip of the main
branch is not accidental. For these cases, just add a comment such as
`# noqa: latest` to the same line to prevent it from triggering.

## Possible errors messages:

- `latest[git]`
- `latest[hg]`

## Problematic code

```yaml
---
- name: Example for `latest` rule
  hosts: localhost
  tasks:
    - name: Risky use of git module
      ansible.builtin.git:
        repo: "https://github.com/ansible/ansible-lint"
        version: HEAD # <-- HEAD value is triggering the rule
```

## Correct code

```yaml
---
- name: Example for `latest` rule
  hosts: localhost
  tasks:
    - name: Safe use of git module
      ansible.builtin.git:
        repo: "https://github.com/ansible/ansible-lint"
        version: abcd1234... # <-- that is safe
```
