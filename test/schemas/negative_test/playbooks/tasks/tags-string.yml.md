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
    "instancePath": "/0/tags",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/tags/anyOf/0/type"
  },
  {
    "instancePath": "/0/tags",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/$defs/tags/anyOf/1/type"
  },
  {
    "instancePath": "/0/tags",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/$defs/tags/anyOf"
  },
  {
    "instancePath": "/0/tags",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/tags/anyOf/0/type"
  },
  {
    "instancePath": "/0/tags",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/$defs/tags/anyOf/1/type"
  },
  {
    "instancePath": "/0/tags",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/$defs/tags/anyOf"
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
      "filename": "negative_test/playbooks/tasks/tags-string.yml",
      "path": "$[0]",
      "message": "{'ansible.builtin.debug': {'msg': 'foo'}, 'tags': 123} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].tags",
        "message": "123 is not of type 'string'"
      },
      "num_sub_errors": 6,
      "sub_errors": [
        {
          "path": "$[0].tags",
          "message": "123 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tags",
          "message": "123 is not of type 'string'"
        },
        {
          "path": "$[0].tags",
          "message": "123 is not of type 'array'"
        },
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].tags",
          "message": "123 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tags",
          "message": "123 is not of type 'string'"
        },
        {
          "path": "$[0].tags",
          "message": "123 is not of type 'array'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
