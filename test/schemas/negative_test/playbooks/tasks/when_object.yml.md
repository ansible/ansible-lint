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
    "instancePath": "/0/when",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/0/type"
  },
  {
    "instancePath": "/0/when",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/1/type"
  },
  {
    "instancePath": "/0/when",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/type"
  },
  {
    "instancePath": "/0/when",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf"
  },
  {
    "instancePath": "/0/when",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/0/type"
  },
  {
    "instancePath": "/0/when",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/1/type"
  },
  {
    "instancePath": "/0/when",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/type"
  },
  {
    "instancePath": "/0/when",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf"
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
      "filename": "negative_test/playbooks/tasks/when_object.yml",
      "path": "$[0]",
      "message": "{'action': 'foo', 'when': {}} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].when",
        "message": "{} is not of type 'boolean'"
      },
      "num_sub_errors": 8,
      "sub_errors": [
        {
          "path": "$[0].when",
          "message": "{} is not valid under any of the given schemas"
        },
        {
          "path": "$[0].when",
          "message": "{} is not of type 'boolean'"
        },
        {
          "path": "$[0].when",
          "message": "{} is not of type 'string'"
        },
        {
          "path": "$[0].when",
          "message": "{} is not of type 'array'"
        },
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].when",
          "message": "{} is not valid under any of the given schemas"
        },
        {
          "path": "$[0].when",
          "message": "{} is not of type 'boolean'"
        },
        {
          "path": "$[0].when",
          "message": "{} is not of type 'string'"
        },
        {
          "path": "$[0].when",
          "message": "{} is not of type 'array'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
