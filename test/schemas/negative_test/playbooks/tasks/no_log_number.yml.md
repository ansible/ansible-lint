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
    "instancePath": "/0/no_log",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/no_log",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/oneOf/1/type"
  },
  {
    "instancePath": "/0/no_log",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/no_log",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0/no_log",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/no_log",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/oneOf/1/type"
  },
  {
    "instancePath": "/0/no_log",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/no_log",
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
      "filename": "negative_test/playbooks/tasks/no_log_number.yml",
      "path": "$[0]",
      "message": "{'ansible.builtin.debug': {'msg': 'foo'}, 'no_log': 123} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].no_log",
        "message": "123 is not of type 'boolean'"
      },
      "num_sub_errors": 6,
      "sub_errors": [
        {
          "path": "$[0].no_log",
          "message": "123 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].no_log",
          "message": "123 is not of type 'boolean'"
        },
        {
          "path": "$[0].no_log",
          "message": "123 is not of type 'string'"
        },
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].no_log",
          "message": "123 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].no_log",
          "message": "123 is not of type 'boolean'"
        },
        {
          "path": "$[0].no_log",
          "message": "123 is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
