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
      "additionalProperty": "gather_facts"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "tasks"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0/tasks/0",
    "keyword": "required",
    "message": "must have required property 'block'",
    "params": {
      "missingProperty": "block"
    },
    "schemaPath": "#/required"
  },
  {
    "instancePath": "/0/tasks/0/when",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/0/type"
  },
  {
    "instancePath": "/0/tasks/0/when",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/1/type"
  },
  {
    "instancePath": "/0/tasks/0/when/1",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/items/anyOf/0/type"
  },
  {
    "instancePath": "/0/tasks/0/when/1",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/items/anyOf/1/type"
  },
  {
    "instancePath": "/0/tasks/0/when/1",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/items/anyOf"
  },
  {
    "instancePath": "/0/tasks/0/when",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf"
  },
  {
    "instancePath": "/0/tasks/0/when",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/0/type"
  },
  {
    "instancePath": "/0/tasks/0/when",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/1/type"
  },
  {
    "instancePath": "/0/tasks/0/when/1",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/items/anyOf/0/type"
  },
  {
    "instancePath": "/0/tasks/0/when/1",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/items/anyOf/1/type"
  },
  {
    "instancePath": "/0/tasks/0/when/1",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/$defs/complex_conditional/oneOf/2/items/anyOf"
  },
  {
    "instancePath": "/0/tasks/0/when",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/$defs/complex_conditional/oneOf"
  },
  {
    "instancePath": "/0/tasks/0",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/items/anyOf"
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
      "filename": "negative_test/playbooks/when.yml",
      "path": "$[0]",
      "message": "{'name': 'Test for when (failure)', 'hosts': 'localhost', 'gather_facts': False, 'tasks': [{'name': 'Testing for when is passed a list', 'ansible.builtin.debug': {'msg': 'this is ok'}, 'when': [True, 123]}]} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'gather_facts', 'hosts', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].tasks[0].when[1]",
        "message": "123 is not of type 'boolean'"
      },
      "num_sub_errors": 17,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'gather_facts', 'hosts', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'name': 'Test for when (failure)', 'hosts': 'localhost', 'gather_facts': False, 'tasks': [{'name': 'Testing for when is passed a list', 'ansible.builtin.debug': {'msg': 'this is ok'}, 'when': [True, 123]}]} is not valid under any of the given schemas"
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
          "path": "$[0].tasks[0]",
          "message": "{'name': 'Testing for when is passed a list', 'ansible.builtin.debug': {'msg': 'this is ok'}, 'when': [True, 123]} is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].when",
          "message": "[True, 123] is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].when",
          "message": "[True, 123] is not of type 'boolean'"
        },
        {
          "path": "$[0].tasks[0].when",
          "message": "[True, 123] is not of type 'string'"
        },
        {
          "path": "$[0].tasks[0].when[1]",
          "message": "123 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].when[1]",
          "message": "123 is not of type 'boolean'"
        },
        {
          "path": "$[0].tasks[0].when[1]",
          "message": "123 is not of type 'string'"
        },
        {
          "path": "$[0].tasks[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].tasks[0].when",
          "message": "[True, 123] is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].when",
          "message": "[True, 123] is not of type 'boolean'"
        },
        {
          "path": "$[0].tasks[0].when",
          "message": "[True, 123] is not of type 'string'"
        },
        {
          "path": "$[0].tasks[0].when[1]",
          "message": "123 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].when[1]",
          "message": "123 is not of type 'boolean'"
        },
        {
          "path": "$[0].tasks[0].when[1]",
          "message": "123 is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
