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
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/oneOf/1/type"
  },
  {
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/oneOf/0/type"
  },
  {
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/oneOf/1/type"
  },
  {
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/tasks/0/run_once",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
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
      "filename": "negative_test/playbooks/run_once_list.yml",
      "path": "$[0]",
      "message": "{'hosts': 'localhost', 'tasks': [{'name': 'foo2', 'ansible.builtin.debug': {'msg': 'foo!'}, 'run_once': ['{{ true }}', 'xxx']}]} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'hosts', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].tasks[0].run_once",
        "message": "['{{ true }}', 'xxx'] is not of type 'boolean'"
      },
      "num_sub_errors": 11,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'hosts', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'hosts': 'localhost', 'tasks': [{'name': 'foo2', 'ansible.builtin.debug': {'msg': 'foo!'}, 'run_once': ['{{ true }}', 'xxx']}]} is not valid under any of the given schemas"
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
          "message": "{'name': 'foo2', 'ansible.builtin.debug': {'msg': 'foo!'}, 'run_once': ['{{ true }}', 'xxx']} is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].run_once",
          "message": "['{{ true }}', 'xxx'] is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].run_once",
          "message": "['{{ true }}', 'xxx'] is not of type 'boolean'"
        },
        {
          "path": "$[0].tasks[0].run_once",
          "message": "['{{ true }}', 'xxx'] is not of type 'string'"
        },
        {
          "path": "$[0].tasks[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].tasks[0].run_once",
          "message": "['{{ true }}', 'xxx'] is not valid under any of the given schemas"
        },
        {
          "path": "$[0].tasks[0].run_once",
          "message": "['{{ true }}', 'xxx'] is not of type 'boolean'"
        },
        {
          "path": "$[0].tasks[0].run_once",
          "message": "['{{ true }}', 'xxx'] is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
