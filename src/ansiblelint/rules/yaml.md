# yaml

This rule checks YAML syntax and is an implementation of `yamllint`.

You can disable YAML syntax violations by adding `yaml` to the `skip_list`
in your Ansible-lint configuration as follows:

```yaml
skip_list:
  - yaml
```

For more fine-grained control, disable violations for specific rules using tag
identifiers in the `yaml[yamllint_rule]` format as follows:

```yaml
skip_list:
  - yaml[trailing-spaces]
  - yaml[indentation]
```

If you want Ansible-lint to report YAML syntax violations as warnings, and not
fatal errors, add tag identifiers to the `warn_list` in your configuration, for example:

```yaml
warn_list:
  - yaml[document-start]
```

See the [list of yamllint rules](https://yamllint.readthedocs.io/en/stable/rules.html) for more information.

## Problematic code

```yaml
# Missing YAML document start.
foo: ...
foo: ...  # <-- Duplicate key.
bar: ...       # <-- Incorrect comment indentation
```

## Correct code

```yaml
---
foo: ...
bar: ... # Correct comment indentation.
```
