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
      "additionalProperty": "validate_argspec"
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
    "instancePath": "/0/validate_argspec",
    "keyword": "type",
    "message": "must be boolean",
    "params": {
      "type": "boolean"
    },
    "schemaPath": "#/properties/validate_argspec/oneOf/0/type"
  },
  {
    "instancePath": "/0/validate_argspec",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/validate_argspec/oneOf/1/type"
  },
  {
    "instancePath": "/0/validate_argspec",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/properties/validate_argspec/oneOf"
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
      "filename": "negative_test/playbooks/validate_argspec.yml",
      "path": "$[0]",
      "message": "{'hosts': 'localhost', 'gather_facts': False, 'validate_argspec': 42, 'tasks': [{'ansible.builtin.debug': {'msg': 'foo'}}]} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'gather_facts', 'hosts', 'tasks', 'validate_argspec' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].validate_argspec",
        "message": "42 is not of type 'boolean'"
      },
      "num_sub_errors": 6,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'gather_facts', 'hosts', 'tasks', 'validate_argspec' do not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'hosts': 'localhost', 'gather_facts': False, 'validate_argspec': 42, 'tasks': [{'ansible.builtin.debug': {'msg': 'foo'}}]} is not valid under any of the given schemas"
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
          "path": "$[0].validate_argspec",
          "message": "42 is not valid under any of the given schemas"
        },
        {
          "path": "$[0].validate_argspec",
          "message": "42 is not of type 'boolean'"
        },
        {
          "path": "$[0].validate_argspec",
          "message": "42 is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
