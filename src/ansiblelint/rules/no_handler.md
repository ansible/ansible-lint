# no-handler

This rule checks for the correct handling of changes to results or conditions.

- Use the `when` clause to detect a result or condition.
- Use the `changed_when` clause to handle changes to a result or condition.

## Problematic Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Put YAML file in an S3 bucket
      amazon.aws.aws_s3:
        bucket: "my_bucket"
        mode: put
        object: "file.yaml"
        src: "/home/user/file.yaml"
      register: result
      when: result.changed # <- Uses the when clause as a handler.
```

## Correct Code

```yaml
---
- name: Example playbook
  hosts: localhost
  tasks:
    - name: Put YAML file in an S3 bucket
      amazon.aws.aws_s3:
        bucket: "my_bucket"
        mode: put
        object: "file.yaml"
        src: "/home/user/file.yaml"
      register: result
      changed_when: result.changed # <- Uses the changed_when clause as a handler.
```
