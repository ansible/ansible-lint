## jinja

This rule can report problems related to jinja2 string templates. The current
version can report `jinja[spacing]` when there are no spaces between variables
and operators, including filters, like `{{ var_name | filter }}`. This
improves readability and makes it less likely to introduce typos.

### Problematic code

```yaml
---
foo: "{{some|dict2items}}"
```

### Correct code

```yaml
---
foo: "{{ some | dict2items }}"
```
