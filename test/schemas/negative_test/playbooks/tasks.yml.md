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
      "additionalProperty": "pre_tasks"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "post_tasks"
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
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "handlers"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0/handlers",
    "keyword": "type",
    "message": "must be array,null",
    "params": {
      "type": [
        "array",
        "null"
      ]
    },
    "schemaPath": "#/type"
  },
  {
    "instancePath": "/0/post_tasks",
    "keyword": "type",
    "message": "must be array,null",
    "params": {
      "type": [
        "array",
        "null"
      ]
    },
    "schemaPath": "#/type"
  },
  {
    "instancePath": "/0/pre_tasks",
    "keyword": "type",
    "message": "must be array,null",
    "params": {
      "type": [
        "array",
        "null"
      ]
    },
    "schemaPath": "#/type"
  },
  {
    "instancePath": "/0/tasks",
    "keyword": "type",
    "message": "must be array,null",
    "params": {
      "type": [
        "array",
        "null"
      ]
    },
    "schemaPath": "#/type"
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
      "filename": "negative_test/playbooks/tasks.yml",
      "path": "$[0]",
      "message": "{'hosts': 'localhost', 'pre_tasks': 'foo', 'post_tasks': {}, 'tasks': 1, 'handlers': 1.0} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'handlers', 'hosts', 'post_tasks', 'pre_tasks', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].handlers",
        "message": "1.0 is not of type 'array', 'null'"
      },
      "num_sub_errors": 7,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'handlers', 'hosts', 'post_tasks', 'pre_tasks', 'tasks' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'hosts': 'localhost', 'pre_tasks': 'foo', 'post_tasks': {}, 'tasks': 1, 'handlers': 1.0} is not valid under any of the given schemas"
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
          "path": "$[0].handlers",
          "message": "1.0 is not of type 'array', 'null'"
        },
        {
          "path": "$[0].post_tasks",
          "message": "{} is not of type 'array', 'null'"
        },
        {
          "path": "$[0].pre_tasks",
          "message": "'foo' is not of type 'array', 'null'"
        },
        {
          "path": "$[0].tasks",
          "message": "1 is not of type 'array', 'null'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
