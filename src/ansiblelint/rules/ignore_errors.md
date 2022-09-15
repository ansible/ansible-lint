# ignore-errors

This rule checks that playbooks do not use the `ignore_errors` directive to ignore all errors.
Ignoring all errors in a playbook hides actual failures, incorrectly mark tasks as failed, and result in unexpected side effects and behavior.

Instead of using the `ignore_errors: true` directive, you should do the following:

- Ignore errors only when using the `{{ ansible_check_mode }}` variable.
- Use `register` to register errors.
- Use `failed_when:` and specify acceptable error conditions.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Run apt-get update
      ansible.builtin.command: apt-get update
      ignore_errors: true # <- Ignores all errors, including important failures.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Run apt-get update
      ansible.builtin.command: apt-get update
      ignore_errors: "{{ ansible_check_mode }}" # <- Ignores errors in check mode.
```

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Run apt-get update
      ansible.builtin.command: apt-get update
      ignore_errors: true
      register: ignore_errors_register # <- Stores errors and failures for evaluation.
```

```yaml
---
- name: Example playbook
  hosts: all
  tasks:
    - name: Disable apport
      become: "yes"
      lineinfile:
        line: "enabled=0"
        dest: /etc/default/apport
        mode: 0644
        state: present
      register: default_apport
      failed_when: default_apport.rc !=0 and not default_apport.rc == 257 # <- Defines conditions that constitute a failure.
```
