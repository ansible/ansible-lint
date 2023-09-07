# ajv errors

```json
[
  {
    "instancePath": "/profile",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "min",
        "basic",
        "moderate",
        "safety",
        "shared",
        "production",
        null
      ]
    },
    "schemaPath": "#/properties/profile/enum"
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
      "filename": "negative_test/.config/ansible-lint.yml",
      "path": "$.profile",
      "message": "'invalid_profile' is not one of ['min', 'basic', 'moderate', 'safety', 'shared', 'production', None]",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
