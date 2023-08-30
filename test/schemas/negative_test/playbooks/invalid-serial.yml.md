# ajv errors

```json
[
  {
    "instancePath": "/0",
    "keyword": "required",
    "message": "must have required property 'ansible.builtin.import_playbook'",
    "params": {
      "missingProperty": "ansible.builtin.import_playbook"
    },
    "schemaPath": "#/oneOf/0/required"
  },
  {
    "instancePath": "/0",
    "keyword": "required",
    "message": "must have required property 'import_playbook'",
    "params": {
      "missingProperty": "import_playbook"
    },
    "schemaPath": "#/oneOf/1/required"
  },
  {
    "instancePath": "/0",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "hosts"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "serial"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0/serial",
    "keyword": "type",
    "message": "must be integer",
    "params": {
      "type": "integer"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/serial",
    "keyword": "pattern",
    "message": "must match pattern \"^\\d+\\.?\\d*%?$\"",
    "params": {
      "pattern": "^\\d+\\.?\\d*%?$"
    },
    "schemaPath": "#/oneOf/1/pattern"
  },
  {
    "instancePath": "/0/serial",
    "keyword": "pattern",
    "message": "must match pattern \"^\\{[\\{%](.|[\r\n])*[\\}%]\\}$\"",
    "params": {
      "pattern": "^\\{[\\{%](.|[\r\n])*[\\}%]\\}$"
    },
    "schemaPath": "#/$defs/full-jinja/pattern"
  },
  {
    "instancePath": "/0/serial",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0/serial",
    "keyword": "type",
    "message": "must be array",
    "params": {
      "type": "array"
    },
    "schemaPath": "#/properties/serial/anyOf/1/type"
  },
  {
    "instancePath": "/0/serial",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/properties/serial/anyOf"
  },
  {
    "instancePath": "/0",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/items/oneOf"
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
      "filename": "negative_test/playbooks/invalid-serial.yml",
      "path": "$[0]",
      "message": "{'hosts': 'localhost', 'serial': '10%BAD'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'hosts', 'serial' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].serial",
        "message": "'10%BAD' is not of type 'integer'"
      },
      "num_sub_errors": 9,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'hosts', 'serial' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'hosts': 'localhost', 'serial': '10%BAD'} is not valid under any of the given schemas"
        },
        {
          "path": "$[0]",
          "message": "'ansible.builtin.import_playbook' is a required property"
        },
        {
          "path": "$[0]",
          "message": "'import_playbook' is a required property"
        },
        {
          "path": "$[0].serial",
          "message": "'10%BAD' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].serial",
          "message": "'10%BAD' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].serial",
          "message": "'10%BAD' is not of type 'integer'"
        },
        {
          "path": "$[0].serial",
          "message": "'10%BAD' does not match '^\\\\d+\\\\.?\\\\d*%?$'"
        },
        {
          "path": "$[0].serial",
          "message": "'10%BAD' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
        },
        {
          "path": "$[0].serial",
          "message": "'10%BAD' is not of type 'array'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
