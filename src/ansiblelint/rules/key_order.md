# key-order

This rule recommends reordering key names in ansible content to make
code easier to maintain and less prone to errors.

Here are some examples of common ordering checks done for tasks and handlers:

- `name` must always be the first key for plays, tasks and handlers
- on tasks, the `block`, `rescue` and `always` keys must be the last keys,
  as this would avoid accidental miss-indentation errors between the last task
  and the parent level.

## Problematic code

```yaml
---
- hosts: localhost
  name: This is a playbook # <-- name key should be the first one
  tasks:
    - name: A block
      block:
        - name: Display a message
          debug:
            msg: "Hello world!"
      when: true # <-- when key should be before block
```

## Correct code

```yaml
---
- name: This is a playbook
  hosts: localhost
  tasks:
    - name: A block
      when: true
      block:
        - name: Display a message
          debug:
            msg: "Hello world!"
```

## Reasoning

Making decisions about the optimal order of keys for ansible tasks or plays is
no easy task, as we had a huge number of combinations to consider. This is also
the reason why we started with a minimal sorting rule (name to be the first),
and aimed to gradually add more fields later, and only when we find the proofs
that one approach is likely better than the other.

### Why I no longer can put `when` after a `block`?

Try to remember that in real life, `block/rescue/always` have the habit to
grow due to the number of tasks they host inside, making them exceed what a single screen. This would move the `when` task further away from the rest of the task properties. A `when` from the last task inside the block can
easily be confused as being at the block level, or the reverse. When tasks are
moved from one location to another, there is a real risk of moving the block
level when with it.

By putting the `when` before the `block`, we avoid that kind of risk. The same risk applies to any simple property at the task level, so that is why
we concluded that the block keys must be the last ones.

Another common practice was to put `tags` as the last property. Still, for the
same reasons, we decided that they should not be put after block keys either.

!!! note

    This rule can be automatically fixed using [`--fix`](../autofix.md) option.
