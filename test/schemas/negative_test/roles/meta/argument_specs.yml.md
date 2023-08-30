# ajv errors

```json
[
  {
    "instancePath": "/argument_specs/main",
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
      "filename": "negative_test/roles/meta/argument_specs.yml",
      "path": "$.argument_specs.main",
      "message": "Additional properties are not allowed ('foo' was unexpected)",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
