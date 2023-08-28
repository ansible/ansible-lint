# ajv errors

```json
[
  {
    "instancePath": "/requires_ansible",
    "keyword": "pattern",
    "message": "must match pattern \"^[^\\s]*$\"",
    "params": {
      "pattern": "^[^\\s]*$"
    },
    "schemaPath": "#/properties/requires_ansible/pattern"
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
      "filename": "negative_test/meta/runtime.yml",
      "path": "$.requires_ansible",
      "message": "'>= 2.12' does not match '^[^\\\\s]*$'",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
