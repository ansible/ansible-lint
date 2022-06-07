## var-spacing

Variables and filters in Jinja2 should have spaces before and after, like
`{{ var_name | filter }}.`. This improves readability and makes it
less likely to introduce typos.

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
