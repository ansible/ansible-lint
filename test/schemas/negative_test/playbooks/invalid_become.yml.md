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
      "additionalProperty": "become"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0/become",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/become",
    "keyword": "pattern",
    "message": "must match pattern \"^\\{[\\{%](.|[\r\n])*[\\}%]\\}$\"",
    "params": {
      "pattern": "^\\{[\\{%](.|[\r\n])*[\\}%]\\}$"
    },
    "schemaPath": "#/$defs/full-jinja/pattern"
  },
  {
    "instancePath": "/0/become",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
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
      "filename": "negative_test/playbooks/invalid_become.yml",
      "path": "$[0]",
      "message": "{'hosts': 'localhost', 'become': 'yes'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'become', 'hosts' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].become",
        "message": "'yes' is not of type 'boolean'"
      },
      "num_sub_errors": 6,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'become', 'hosts' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'hosts': 'localhost', 'become': 'yes'} is not valid under any of the given schemas"
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
          "path": "$[0].become",
          "message": "'yes' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].become",
          "message": "'yes' is not of type 'boolean'"
        },
        {
          "path": "$[0].become",
          "message": "'yes' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
