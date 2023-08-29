# ajv errors

```json
[
  {
    "instancePath": "",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/anyOf/0/type"
  },
  {
    "instancePath": "",
    "keyword": "required",
    "message": "must have required property 'collections'",
    "params": {
      "missingProperty": "collections"
    },
    "schemaPath": "#/anyOf/0/required"
  },
  {
    "instancePath": "",
    "keyword": "required",
    "message": "must have required property 'roles'",
    "params": {
      "missingProperty": "roles"
    },
    "schemaPath": "#/anyOf/1/required"
  },
  {
    "instancePath": "",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/anyOf"
  },
  {
    "instancePath": "",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "foo"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/anyOf"
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
      "filename": "negative_test/reqs3/meta/requirements.yml",
      "path": "$",
      "message": "{'foo': 'bar'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$",
        "message": "{'foo': 'bar'} is not of type 'array'"
      },
      "best_deep_match": {
        "path": "$",
        "message": "{'foo': 'bar'} is not of type 'array'"
      },
      "num_sub_errors": 4,
      "sub_errors": [
        {
          "path": "$",
          "message": "{'foo': 'bar'} is not of type 'array'"
        },
        {
          "path": "$",
          "message": "Additional properties are not allowed ('foo' was unexpected)"
        },
        {
          "path": "$",
          "message": "{'foo': 'bar'} is not valid under any of the given schemas"
        },
        {
          "path": "$",
          "message": "'collections' is a required property"
        },
        {
          "path": "$",
          "message": "'roles' is a required property"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
