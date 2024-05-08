# yaml

This rule checks YAML syntax by using [yamllint] library but with a
[specific default configuration](#yamllint-configuration), one that is
compatible with both, our internal reformatter (`--fix`) and also [prettier].

You can disable YAML syntax violations by adding `yaml` to the `skip_list` in
your Ansible-lint configuration as follows:

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
fatal errors, add tag identifiers to the `warn_list` in your configuration, for
example:

```yaml
warn_list:
  - yaml[document-start]
```

!!! warning

    You cannot use `tags: [skip_ansible_lint]` to disable this rule but you can
    use [yamllint magic comments](https://yamllint.readthedocs.io/en/stable/disable_with_comments.html#disabling-checks-for-all-or-part-of-the-file) for tuning it.

See the
[list of yamllint rules](https://yamllint.readthedocs.io/en/stable/rules.html)
for more information.

Some of the detailed error codes that you might see are:

- `yaml[brackets]` - _too few spaces inside empty brackets_, or _too many spaces
  inside brackets_
- `yaml[colons]` - _too many spaces before colon_, or _too many spaces after
  colon_
- `yaml[commas]` - _too many spaces before comma_, or _too few spaces after
  comma_
- `yaml[comments-indentation]` - _Comment not indented like content_
- `yaml[comments]` - _Too few spaces before comment_, or _Missing starting space
  in comment_
- `yaml[document-start]` - _missing document start "---"_ or _found forbidden
  document start "---"_
- `yaml[empty-lines]` - _too many blank lines (...> ...)_
- `yaml[indentation]` - _Wrong indentation: expected ... but found ..._
- `yaml[key-duplicates]` - _Duplication of key "..." in mapping_
- `yaml[line-length]` - _Line too long (... > ... characters)_
- `yaml[new-line-at-end-of-file]` - _No new line character at the end of file_
- `yaml[octal-values]`: forbidden implicit or explicit [octal](#octals) value
- `yaml[syntax]` - YAML syntax is broken
- `yaml[trailing-spaces]` - Spaces are found at the end of lines
- `yaml[truthy]` - _Truthy value should be one of ..._

## Octals

As [YAML specification] regarding octal values changed at least 3 times in
[1.1], [1.2.0] and [1.2.2] we now require users to always add quotes around
octal values, so the YAML loaders will all load them as strings, providing a
consistent behavior. This is also safer as JSON does not support octal values
either.

By default, yamllint does not check for octals but our custom default ruleset
for it does check these. If for some reason, you do not want to follow our
defaults, you can create a `.yamllint` file in your project and this will take
precedence over our defaults.

## Additional Information for Multiline Strings

Adhering to yaml[line-length] rule, for writing multiline strings we recommend
using Block Style Indicator: literal style indicated by a pipe (|) or folded
style indicated by a right angle bracket (>), instead of escaping the newlines
with backslashes. Reference [guide] for writing multiple line strings in yaml.

## Problematic code

```yaml
# Missing YAML document start.
foo: 0777 # <-- yaml[octal-values]
foo2: 0o777 # <-- yaml[octal-values]
foo2: ... # <-- yaml[key-duplicates]
bar: ...       # <-- yaml[comments-indentation]
```

## Correct code

```yaml
---
foo: "0777" # <-- Explicitly quoting octal is less risky.
foo2: "0o777" # <-- Explicitly quoting octal is less risky.
bar: ... # Correct comment indentation.
```

## Yamllint configuration

If you decide to add a custom yamllint config to your project, ansible-lint
might refuse to run if it detects that some of your options are incompatible and
ask you to correct them. When this happens, you will see a message like the one
below:

```
CRITICAL Found incompatible custom yamllint configuration (.yamllint), please either remove the file or edit it to comply with:
  - comments.min-spaces-from-content must be 1
  - braces.min-spaces-inside must be 0
  - braces.max-spaces-inside must be 1
  - octal-values.forbid-implicit-octal must be true
  - octal-values.forbid-explicit-octal must be true

Read https://ansible.readthedocs.io/projects/lint/rules/yaml/ for more details regarding why we have these requirements.
```

!!! warning

    [Auto-fix](../autofix.md) functionality will change **inline comment indentation to one
    character instead of two**, which is the default of [yamllint]. The reason
    for this decision was to keep reformatting compatibility
    with [prettier], which is the most popular reformatter.

    ```yaml title=".yamllint"
    rules:
      comments:
        min-spaces-from-content: 1 # prettier compatibility
    ```

    There is no need to create this yamllint config file, but if you also
    run yamllint yourself, you might want to create it to make it behave
    the same way as ansible-lint.

Below you can find the default yamllint configuration that our linter will use
when there is no custom file present.

```yaml
{!../src/ansiblelint/data/.yamllint!}
```

[1.1]: https://yaml.org/spec/1.1/
[1.2.0]: https://yaml.org/spec/1.2.0/
[1.2.2]: https://yaml.org/spec/1.2.2/
[yaml specification]: https://yaml.org/
[guide]:
  https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html#yaml-basics
[prettier]: https://prettier.io/
[yamllint]: https://yamllint.readthedocs.io/en/stable/
