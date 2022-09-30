```{include} ../.github/CONTRIBUTING.md
   :end-before: DO-NOT-REMOVE-deps-snippet-PLACEHOLDER
```

# Module dependency graph

Extra care should be taken when considering adding any dependency. Removing
most dependencies on Ansible internals is desired as these can change
without any warning.

```{command-output} _PIP_USE_IMPORTLIB_METADATA=0 pipdeptree -p ansible-lint
  :shell:

```

# Adding a new rule

Writing a new rule is as easy as adding a single new rule, one that combines
**implementation, testing and documentation**.

One good example is [MetaTagValidRule] which can easily be copied in order
to create a new rule by following the steps below:

- Use a short but clear class name, which must match the filename
- Pick an unused `id`, the first number is used to determine rule section.
  Look at [rules](rules.md) page and pick one that matches the best
  your new rule and ee which one fits best.
- Include `experimental` tag. Any new rule must stay as
  experimental for at least two weeks until this tag is removed in next major
  release.
- Update all class level variables.
- Implement linting methods needed by your rule, these are those starting with
  **match** prefix. Implement only those you need. For the moment you will need
  to look at how similar rules were implemented to figure out what to do.
- Update the tests. It must have at least one test and likely also a negative
  match one.
- If the rule is task specific, it may be best to include a test to verify its
  use inside blocks as well.
- Optionally run only the rule specific tests with a command like:
  {command}`tox -e py38-core -- -k NewRule`
- Run {command}`tox` in order to run all ansible-lint tests. Adding a new rule
  can break some other tests. Update them if needed.
- Run {command}`ansible-lint -L` and check that the rule description renders
  correctly.
- Build the docs using {command}`tox -e docs` and check that the new rule is
  displayed correctly in them.

[metatagvalidrule]: https://github.com/ansible/ansible-lint/blob/main/src/ansiblelint/rules/meta_no_tags.py
