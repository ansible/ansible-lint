## yaml

Our linter also includes violations reported by [yamllint](https://github.com/adrienverge/yamllint)
but it uses a slightly different default configuration. We will still load
custom yamllint configuration files, but the defaults come from
ansible-lint, not from yamllint.

You can fully disable all yamllint violations by adding `yaml` to the `skip_list`.

Specific tag identifiers that are printed at the end of rule name,
like `yaml[trailing-spaces]` or `yaml[indentation]` can also be be skipped, allowing
you to have a more fine control.

### Problematic code

```yaml
# missing document-start
foo: ...
foo: ...  # <-- key-duplicates
bar: ...       # <-- wrong comment indentation
```

### Correct code

```yaml
---
foo: ...
bar: ... # comment
```
