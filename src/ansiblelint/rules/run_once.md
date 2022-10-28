# run-once

This rule warns against the use of `run_once` when `strategy` is set to `free`.

This rule can produce the following messages:

- `run_once[play]`: Play uses `strategy: free`.
- `run_once[task]`: Using `run_once` may behave differently if `strategy` is set to `free`.

For more information see the following topics in Ansible documentation:

- [free strategy](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/free_strategy.html#free-strategy)
- [selecting a strategy](https://docs.ansible.com/ansible/latest/user_guide/playbooks_strategies.html#selecting-a-strategy)
- [run_once(playbook keyword) more info](https://docs.ansible.com/ansible/latest/reference_appendices/playbooks_keywords.html)

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
