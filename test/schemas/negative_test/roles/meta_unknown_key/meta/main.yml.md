# ajv errors

```json
[
  {
    "instancePath": "",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "foo"
    },
    "schemaPath": "#/additionalProperties"
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
      "filename": "negative_test/roles/meta_unknown_key/meta/main.yml",
      "path": "$",
      "message": "Additional properties are not allowed ('foo' was unexpected)",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
