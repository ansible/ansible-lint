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
  },
  {
    "instancePath": "/galaxy_info/namespace",
    "keyword": "pattern",
    "message": "must match pattern \"^[a-z][a-z0-9_]+$\"",
    "params": {
      "pattern": "^[a-z][a-z0-9_]+$"
    },
    "schemaPath": "#/properties/namespace/pattern"
  }
]
```

# check-jsonschema

stdout:

```json
{
  "status": "fail",
  "errors": [
    {
      "filename": "negative_test/roles/meta_invalid_role_namespace/meta/main.yml",
      "path": "$.galaxy_info",
      "message": "'author' is a required property",
      "has_sub_errors": false
    },
    {
      "filename": "negative_test/roles/meta_invalid_role_namespace/meta/main.yml",
      "path": "$.galaxy_info.namespace",
      "message": "'foo-bar' does not match '^[a-z][a-z0-9_]+$'",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
