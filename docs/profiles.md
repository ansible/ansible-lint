# Profiles

One of the best ways to run `ansible-lint` is by specifying which rule profile
you want to use. These profiles stack on top of each other, allowing you to
gradually raise the quality bar.

To run it with the most strict profile just type `ansible-lint -P production`.

If you want to consult the list of rules from each profile, type
`ansible-lint -P`. For your convenience, we also list the same output below.

The rules that have a '\*' suffix, are not implemented yet but we documented
them with links to their issues.

```{ansible-lint-profile-list}

```
