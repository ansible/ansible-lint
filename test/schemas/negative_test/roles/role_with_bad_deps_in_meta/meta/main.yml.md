# ajv errors

```json
[
  {
    "instancePath": "/dependencies/0",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/dependencies/items/anyOf/0/type"
  },
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
    "instancePath": "/dependencies/0",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/properties/dependencies/items/anyOf"
  },
  {
    "instancePath": "/dependencies/1",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/dependencies/items/anyOf/0/type"
  },
  {
    "instancePath": "/dependencies/1",
    "keyword": "type",
    "message": "must be object",
    "params": {
      "type": "object"
    },
    "schemaPath": "#/type"
  },
  {
    "instancePath": "/dependencies/1",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/properties/dependencies/items/anyOf"
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
  "successes": [],
  "errors": [
    {
      "filename": "negative_test/roles/role_with_bad_deps_in_meta/meta/main.yml",
      "path": "$.dependencies[0]",
      "message": "{'version': 'foo'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$.dependencies[0]",
        "message": "{'version': 'foo'} is not of type 'string'"
      },
      "best_deep_match": {
        "path": "$.dependencies[0]",
        "message": "{'version': 'foo'} is not of type 'string'"
      },
      "num_sub_errors": 4,
      "sub_errors": [
        {
          "path": "$.dependencies[0]",
          "message": "{'version': 'foo'} is not of type 'string'"
        },
        {
          "path": "$.dependencies[0]",
          "message": "{'version': 'foo'} is not valid under any of the given schemas"
        },
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
      "path": "$.dependencies[1]",
      "message": "1234 is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$.dependencies[1]",
        "message": "1234 is not of type 'string'"
      },
      "best_deep_match": {
        "path": "$.dependencies[1]",
        "message": "1234 is not of type 'string'"
      },
      "num_sub_errors": 1,
      "sub_errors": [
        {
          "path": "$.dependencies[1]",
          "message": "1234 is not of type 'string'"
        },
        {
          "path": "$.dependencies[1]",
          "message": "1234 is not of type 'object'"
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
