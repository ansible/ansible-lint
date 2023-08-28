# ajv errors

```json
[
  {
    "instancePath": "",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "release"
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
      "filename": "negative_test/changelogs/unknown-keys/changelogs/changelog.yaml",
      "path": "$",
      "message": "Additional properties are not allowed ('release' was unexpected)",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
