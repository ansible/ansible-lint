## jinja

This rule can report problems related to jinja2 string templates. The current
version can report:

- `jinja[spacing]` when there are no spaces between variables
  and operators, including filters, like `{{ var_name | filter }}`. This
  improves readability and makes it less likely to introduce typos.
- `jinja[invalid]` when the jinja2 template is invalid

As jinja2 syntax is closely following Python one we aim to follow
[black](https://black.readthedocs.io/en/stable/) formatting rules. If you are
curious how black would reformat a small sniped feel free to visit
[online black formatter](https://black.vercel.app/) site. Keep in mind to not
include the entire jinja2 template, so instead of `{{ 1+2==3 }}`, do paste
only `1+2==3`.

### Problematic code

```yaml
---
foo: "{{some|dict2items}}" # <-- jinja[spacing]
bar: "{{ & }}" # <-- jinja[invalid]
```

### Correct code

```yaml
---
foo: "{{ some | dict2items }}"
bar: "{{ '&' }}"
```
