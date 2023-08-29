# ajv errors

```json
[
  {
    "instancePath": "/0",
    "keyword": "required",
    "message": "must have required property 'block'",
    "params": {
      "missingProperty": "block"
    },
    "schemaPath": "#/required"
  },
  {
    "instancePath": "/0/with_items",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/with_items",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/properties/with_items/anyOf/1/type"
  },
  {
    "instancePath": "/0/with_items",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/properties/with_items/anyOf"
  },
  {
    "instancePath": "/0",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/items/anyOf"
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
      "filename": "negative_test/playbooks/tasks/with_items_boolean.yml",
      "path": "$[0]",
      "message": "{'command': 'echo 123', 'with_items': True} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].with_items",
        "message": "True is not of type 'string'"
      },
      "num_sub_errors": 3,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].with_items",
          "message": "True is not valid under any of the given schemas"
        },
        {
          "path": "$[0].with_items",
          "message": "True is not of type 'string'"
        },
        {
          "path": "$[0].with_items",
          "message": "True is not of type 'array'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
