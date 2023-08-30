# ajv errors

```json
[
  {
    "instancePath": "/manifest",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "directive"
    },
    "schemaPath": "#/properties/manifest/additionalProperties"
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
      "filename": "negative_test/galaxy_1/galaxy.yml",
      "path": "$.manifest",
      "message": "Additional properties are not allowed ('directive' was unexpected)",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
