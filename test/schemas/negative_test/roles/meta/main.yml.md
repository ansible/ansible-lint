# ajv errors

```json
[
  {
    "instancePath": "/galaxy_info",
    "keyword": "required",
    "message": "must have required property 'author'",
    "params": {
      "missingProperty": "author"
    },
    "schemaPath": "#/allOf/0/then/required"
  },
  {
    "instancePath": "/galaxy_info",
    "keyword": "if",
    "message": "must match \"then\" schema",
    "params": {
      "failingKeyword": "then"
    },
    "schemaPath": "#/allOf/0/if"
  },
  {
    "instancePath": "/galaxy_info/galaxy_tags",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/properties/galaxy_tags/type"
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
      "filename": "negative_test/roles/meta/main.yml",
      "path": "$.galaxy_info",
      "message": "'author' is a required property",
      "has_sub_errors": false
    },
    {
      "filename": "negative_test/roles/meta/main.yml",
      "path": "$.galaxy_info.galaxy_tags",
      "message": "'database' is not of type 'array'",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
