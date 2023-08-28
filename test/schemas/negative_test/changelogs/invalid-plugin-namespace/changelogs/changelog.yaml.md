# ajv errors

```json
[
  {
    "instancePath": "/releases/1.0.0/plugins/lookup/0/namespace",
    "keyword": "type",
    "message": "must be null",
    "params": {
      "type": "null"
    },
    "schemaPath": "#/$defs/plugin-descriptions/items/properties/namespace/type"
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
      "filename": "negative_test/changelogs/invalid-plugin-namespace/changelogs/changelog.yaml",
      "path": "$.releases.1.0.0.plugins.lookup[0].namespace",
      "message": "'foo' is not of type 'null'",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
