# ajv errors

```json
[
  {
    "instancePath": "/galaxy_info",
    "keyword": "required",
    "message": "must have required property 'author'",
    "params": {
      "missingProperty": "author"
    },
    "schemaPath": "#/allOf/0/then/required"
  },
  {
    "instancePath": "/galaxy_info",
    "keyword": "if",
    "message": "must match \"then\" schema",
    "params": {
      "failingKeyword": "then"
    },
    "schemaPath": "#/allOf/0/if"
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
      "filename": "negative_test/roles/meta_invalid_role_namespace/meta/main.yml",
      "path": "$.galaxy_info",
      "message": "'author' is a required property",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
