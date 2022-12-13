# ajv errors

```json
[
  {
    "instancePath": "",
    "keyword": "type",
    "message": "must be object",
    "params": {
      "type": "object"
    },
    "schemaPath": "#/type"
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
      "filename": "negative_test/changelogs/list/changelog.yml",
      "path": "$",
      "message": "['this is invalid', 'as changelog must be object (mapping)', 'not an array (sequence)'] is not of type 'object'",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
