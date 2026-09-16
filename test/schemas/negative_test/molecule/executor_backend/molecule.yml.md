# ajv errors

```json
[
  {
    "instancePath": "/ansible/executor/backend",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "ansible-playbook",
        "ansible-navigator"
      ]
    },
    "schemaPath": "#/$defs/AnsibleModel/properties/executor/properties/backend/enum"
  }
]
```

# check-jsonschema

stdout:

```json
{
  "status": "fail",
  "successes": [],
  "errors": [
    {
      "filename": "negative_test/molecule/executor_backend/molecule.yml",
      "path": "$.ansible.executor.backend",
      "message": "'not-a-real-backend' is not one of ['ansible-playbook', 'ansible-navigator']",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
