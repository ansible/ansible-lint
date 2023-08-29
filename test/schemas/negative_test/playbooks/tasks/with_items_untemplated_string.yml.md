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
    "keyword": "pattern",
    "message": "must match pattern \"^\\{[\\{%](.|[\r\n])*[\\}%]\\}$\"",
    "params": {
      "pattern": "^\\{[\\{%](.|[\r\n])*[\\}%]\\}$"
    },
    "schemaPath": "#/$defs/full-jinja/pattern"
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
      "filename": "negative_test/playbooks/tasks/with_items_untemplated_string.yml",
      "path": "$[0]",
      "message": "{'command': 'echo 123', 'with_items': 'foobar'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].with_items",
        "message": "'foobar' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
      },
      "num_sub_errors": 3,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].with_items",
          "message": "'foobar' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].with_items",
          "message": "'foobar' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
        },
        {
          "path": "$[0].with_items",
          "message": "'foobar' is not of type 'array'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
