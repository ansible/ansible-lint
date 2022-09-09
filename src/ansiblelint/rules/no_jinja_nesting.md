# no-jinja-nesting

This rule checks for nested Jinja expressions.
Avoid nesting Jinja expressions with curly brackets `{{ }}` inside other Jinja expressions.

An Ansible rule is that "moustaches don't stack".
Nested expressions are an Ansible anti-pattern and do not produce expected results.

## Problematic Code

```yaml
---
{{ list_one + {{ list_two | max }} }}
```

```yaml
---
{{ somevar_{{other_var}} }}
```

## Correct Code

```yaml
---
{ { list_one + max(list_two) } }
```

```yaml
---
# Uses the hostvars variable.
{{ hostvars[inventory_hostname]['somevar_' ~ other_var] }}

# Uses the ansible.builtin.vars lookup plugin.
{{ lookup('vars', 'somevar_' ~ other_var) }}
```
