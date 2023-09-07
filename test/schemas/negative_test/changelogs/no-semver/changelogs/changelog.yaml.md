# ajv errors

```json
[
  {
    "instancePath": "/releases",
    "keyword": "type",
    "message": "must be object",
    "params": {
      "type": "object"
    },
    "schemaPath": "#/properties/releases/type"
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
      "filename": "negative_test/changelogs/no-semver/changelogs/changelog.yaml",
      "path": "$.releases",
      "message": "'foo' is not of type 'object'",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
