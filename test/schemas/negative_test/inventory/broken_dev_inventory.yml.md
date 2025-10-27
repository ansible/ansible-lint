# ajv errors

```json
[
  {
    "instancePath": "/all",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "foo"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/all",
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
      "filename": "negative_test/inventory/broken_dev_inventory.yml",
      "path": "$.all",
      "message": "Additional properties are not allowed ('foo' was unexpected)",
      "has_sub_errors": false
    },
    {
      "filename": "negative_test/inventory/broken_dev_inventory.yml",
      "path": "$.all",
      "message": "Additional properties are not allowed ('foo' was unexpected)",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
