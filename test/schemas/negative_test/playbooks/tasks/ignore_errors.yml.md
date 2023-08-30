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
    "instancePath": "/0/ignore_errors",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/ignore_errors",
    "keyword": "pattern",
    "message": "must match pattern \"^\\{[\\{%](.|[\r\n])*[\\}%]\\}$\"",
    "params": {
      "pattern": "^\\{[\\{%](.|[\r\n])*[\\}%]\\}$"
    },
    "schemaPath": "#/$defs/full-jinja/pattern"
  },
  {
    "instancePath": "/0/ignore_errors",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0/ignore_errors",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/ignore_errors",
    "keyword": "pattern",
    "message": "must match pattern \"^\\{[\\{%](.|[\r\n])*[\\}%]\\}$\"",
    "params": {
      "pattern": "^\\{[\\{%](.|[\r\n])*[\\}%]\\}$"
    },
    "schemaPath": "#/$defs/full-jinja/pattern"
  },
  {
    "instancePath": "/0/ignore_errors",
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
      "filename": "negative_test/playbooks/tasks/ignore_errors.yml",
      "path": "$[0]",
      "message": "{'command': 'echo 123', 'vars': {'should_ignore_errors': True}, 'ignore_errors': 'should_ignore_errors'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].ignore_errors",
        "message": "'should_ignore_errors' is not of type 'boolean'"
      },
      "num_sub_errors": 6,
      "sub_errors": [
        {
          "path": "$[0].ignore_errors",
          "message": "'should_ignore_errors' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].ignore_errors",
          "message": "'should_ignore_errors' is not of type 'boolean'"
        },
        {
          "path": "$[0].ignore_errors",
          "message": "'should_ignore_errors' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
        },
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].ignore_errors",
          "message": "'should_ignore_errors' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].ignore_errors",
          "message": "'should_ignore_errors' is not of type 'boolean'"
        },
        {
          "path": "$[0].ignore_errors",
          "message": "'should_ignore_errors' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
