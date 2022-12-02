# ajv errors

```json
[
  {
    "instancePath": "/dependencies/0",
    "keyword": "required",
    "message": "must have required property 'role'",
    "params": {
      "missingProperty": "role"
    },
    "schemaPath": "#/anyOf/0/required"
  },
  {
    "instancePath": "/dependencies/0",
    "keyword": "required",
    "message": "must have required property 'src'",
    "params": {
      "missingProperty": "src"
    },
    "schemaPath": "#/anyOf/1/required"
  },
  {
    "instancePath": "/dependencies/0",
    "keyword": "required",
    "message": "must have required property 'name'",
    "params": {
      "missingProperty": "name"
    },
    "schemaPath": "#/anyOf/2/required"
  },
  {
    "instancePath": "/dependencies/0",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/anyOf"
  },
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
      "filename": "negative_test/roles/role_with_bad_deps_in_meta/meta/main.yml",
      "path": "$.dependencies[0]",
      "message": "{'version': 'foo'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$.dependencies[0]",
        "message": "'role' is a required property"
      },
      "sub_errors": [
        {
          "path": "$.dependencies[0]",
          "message": "'role' is a required property"
        },
        {
          "path": "$.dependencies[0]",
          "message": "'src' is a required property"
        },
        {
          "path": "$.dependencies[0]",
          "message": "'name' is a required property"
        }
      ]
    },
    {
      "filename": "negative_test/roles/role_with_bad_deps_in_meta/meta/main.yml",
      "path": "$.galaxy_info",
      "message": "'author' is a required property",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
