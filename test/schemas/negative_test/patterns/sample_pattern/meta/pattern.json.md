# ajv errors

```json
[
  {
    "instancePath": "",
    "keyword": "required",
    "message": "must have required property 'name'",
    "params": {
      "missingProperty": "name"
    },
    "schemaPath": "#/required"
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
      "filename": "negative_test/patterns/sample_pattern/meta/pattern.json",
      "path": "$",
      "message": "'name' is a required property",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
