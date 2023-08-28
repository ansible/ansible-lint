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
    "instancePath": "/0/args",
    "keyword": "type",
    "message": "must be object",
    "params": {
      "type": "object"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/args",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/oneOf/1/type"
  },
  {
    "instancePath": "/0/args",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/args",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
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
      "filename": "negative_test/playbooks/tasks/args_integer.yml",
      "path": "$[0]",
      "message": "{'action': 'foo', 'args': 123} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].args",
        "message": "123 is not of type 'object'"
      },
      "num_sub_errors": 3,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].args",
          "message": "123 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].args",
          "message": "123 is not of type 'object'"
        },
        {
          "path": "$[0].args",
          "message": "123 is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
