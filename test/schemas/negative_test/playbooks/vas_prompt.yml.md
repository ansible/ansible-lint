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
    "instancePath": "/0/vars_prompt",
    "keyword": "type",
    "message": "must be object",
    "params": {
      "type": "object"
    },
    "schemaPath": "#/patternProperties/vars/type"
  },
  {
    "instancePath": "/0/vars_prompt/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "tags"
    },
    "schemaPath": "#/$defs/vars_prompt/additionalProperties"
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
      "filename": "negative_test/playbooks/vas_prompt.yml",
      "path": "$[0]",
      "message": "{'hosts': 'localhost', 'vars_prompt': [{'name': 'username', 'prompt': 'What is your username?', 'private': False, 'tags': ['foo']}]} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'hosts' does not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].vars_prompt[0]",
        "message": "Additional properties are not allowed ('tags' was unexpected)"
      },
      "num_sub_errors": 5,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'hosts' does not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'hosts': 'localhost', 'vars_prompt': [{'name': 'username', 'prompt': 'What is your username?', 'private': False, 'tags': ['foo']}]} is not valid under any of the given schemas"
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
          "path": "$[0].vars_prompt",
          "message": "[{'name': 'username', 'prompt': 'What is your username?', 'private': False, 'tags': ['foo']}] is not of type 'object'"
        },
        {
          "path": "$[0].vars_prompt[0]",
          "message": "Additional properties are not allowed ('tags' was unexpected)"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
