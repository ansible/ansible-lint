# run-once

This rule warns against the use of `run_once` when the `strategy` is set to
`free`.

This rule can produce the following messages:

- `run-once[play]`: Play uses `strategy: free`.
- `run-once[task]`: Using `run_once` may behave differently if the `strategy` is
  set to `free`.

For more information see the following topics in Ansible documentation:

- [free strategy](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/free_strategy.html#free-strategy)
- [selecting a strategy](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_strategies.html#selecting-a-strategy)
- [run_once(playbook keyword) more info](https://docs.ansible.com/ansible/latest/reference_appendices/playbooks_keywords.html)

!!! warning

    The reason for the existence of this rule is for reminding users that `run_once`
    is not providing any warranty that the task will run only once.
    This rule will always trigger regardless of the value configured inside the 'strategy' field. That is because the effective value used at runtime can be different than the value inside the file. For example, ansible command line arguments can alter it.

It is perfectly fine to add `# noqa: run-once[task]` to mark the warning as
acknowledged and ignored.

## Problematic Code

```yaml
---
- name: "Example with run_once"
  hosts: all
  strategy: free # <-- avoid use of strategy as free
  gather_facts: false
  tasks:
    - name: Task with run_once
      ansible.builtin.debug:
        msg: "Test"
      run_once: true # <-- avoid use of strategy as free at play level when using run_once at task level
```

## Correct Code

```yaml
- name: "Example without run_once"
  hosts: all
  gather_facts: false
  tasks:
    - name: Task without run_once
      ansible.builtin.debug:
        msg: "Test"
```

```yaml
- name: "Example of using run_once with strategy other than free"
  hosts: all
  strategy: linear
  # strategy: free # noqa: run-once[play] (if using strategy: free can skip it this way)
  gather_facts: false
  tasks: # <-- use noqa to disable rule violations for specific tasks
    - name: Task with run_once # noqa: run-once[task]
      ansible.builtin.debug:
        msg: "Test"
      run_once: true
```
