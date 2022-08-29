# yaml

Our linter also includes violations reported by [yamllint](https://github.com/adrienverge/yamllint)
but it uses a slightly different default configuration. We will still load
custom yamllint configuration files, but the defaults come from
ansible-lint, not from yamllint.

You can fully disable all yamllint violations by adding `yaml` to the `skip_list`.

Specific tag identifiers that are printed at the end of the rule name,
like `yaml[trailing-spaces]` or `yaml[indentation]` can also be skipped, allowing
you to have more control.

Keep in mind that `ansible-lint` does not take into consideration the warning level
of yamllint; we treat all yamllint matches as errors. So, if you want to treat
some of these as warnings, add them to `warn_list`.

## Problematic code

```yaml
# missing document-start
foo: ...
foo: ...  # <-- key-duplicates
bar: ...       # <-- wrong comment indentation
```

## Correct code

```yaml
---
foo: ...
bar: ... # comment
```
