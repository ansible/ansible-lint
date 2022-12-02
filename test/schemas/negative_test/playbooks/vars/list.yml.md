# ajv errors

```json
[
  {
    "instancePath": "",
    "keyword": "type",
    "message": "must be object",
    "params": {
      "type": "object"
    },
    "schemaPath": "#/anyOf/0/type"
  },
  {
    "instancePath": "",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/anyOf/1/type"
  },
  {
    "instancePath": "",
    "keyword": "type",
    "message": "must be null",
    "params": {
      "type": "null"
    },
    "schemaPath": "#/anyOf/2/type"
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
  "errors": [
    {
      "filename": "negative_test/playbooks/vars/list.yml",
      "path": "$",
      "message": "['foo', 'bar'] is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$",
        "message": "['foo', 'bar'] is not of type 'object'"
      },
      "sub_errors": [
        {
          "path": "$",
          "message": "['foo', 'bar'] is not of type 'object'"
        },
        {
          "path": "$",
          "message": "['foo', 'bar'] is not of type 'string'"
        },
        {
          "path": "$",
          "message": "['foo', 'bar'] is not of type 'null'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
