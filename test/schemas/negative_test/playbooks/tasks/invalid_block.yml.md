# ajv errors

```json
[
  {
    "instancePath": "/0/block",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/properties/block/type"
  },
  {
    "instancePath": "/0",
    "keyword": "not",
    "message": "must NOT be valid",
    "params": {},
    "schemaPath": "#/allOf/3/not"
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
      "filename": "negative_test/playbooks/tasks/invalid_block.yml",
      "path": "$[0]",
      "message": "{'block': {}} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "{'block': {}} should not be valid under {'required': ['block']}"
      },
      "best_deep_match": {
        "path": "$[0].block",
        "message": "{} is not of type 'array'"
      },
      "num_sub_errors": 1,
      "sub_errors": [
        {
          "path": "$[0].block",
          "message": "{} is not of type 'array'"
        },
        {
          "path": "$[0]",
          "message": "{'block': {}} should not be valid under {'required': ['block']}"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
