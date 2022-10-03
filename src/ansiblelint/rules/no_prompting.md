# no-prompting

This rule checks for `vars_prompt` or the `ansible.builtin.pause` module in playbooks.
You should enable this rule to ensure that playbooks can run unattended and in CI/CD pipelines.

This is an opt-in rule.
You must enable it in your Ansible-lint configuration as follows:

```yaml
enable_list:
  - no-prompting
```

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  vars_prompt: # <- Prompts the user to input credentials.
    - name: username
      prompt: What is your username?
      private: false

    - name: password
      prompt: What is your password?
  tasks:
    - name: Pause for 5 minutes
      ansible.builtin.pause:
        minutes: 5 # <- Pauses playbook execution for a set period of time.
```

## Correct Code

Correct code for this rule is to omit `vars_prompt` and the `ansible.builtin.pause` module from your playbook.
