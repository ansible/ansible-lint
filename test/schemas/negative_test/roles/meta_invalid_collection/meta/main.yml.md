# ajv errors

```json
[
  {
    "instancePath": "/collections/0",
    "keyword": "pattern",
    "message": "must match pattern \"^[a-z_]+\\.[a-z_]+$\"",
    "params": {
      "pattern": "^[a-z_]+\\.[a-z_]+$"
    },
    "schemaPath": "#/$defs/collections/items/pattern"
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
      "filename": "negative_test/roles/meta_invalid_collection/meta/main.yml",
      "path": "$.collections[0]",
      "message": "'foo' does not match '^[a-z_]+\\\\.[a-z_]+$'",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
