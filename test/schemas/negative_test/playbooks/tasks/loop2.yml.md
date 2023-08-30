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
    "instancePath": "/0/loop",
    "keyword": "type",
    "message": "must be string,array",
    "params": {
      "type": [
        "string",
        "array"
      ]
    },
    "schemaPath": "#/properties/loop/type"
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
      "filename": "negative_test/playbooks/tasks/loop2.yml",
      "path": "$[0]",
      "message": "{'ansible.builtin.debug': {'var': 'item'}, 'loop': 123} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].loop",
        "message": "123 is not of type 'string', 'array'"
      },
      "num_sub_errors": 1,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].loop",
          "message": "123 is not of type 'string', 'array'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
