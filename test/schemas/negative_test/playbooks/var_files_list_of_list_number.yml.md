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
    "instancePath": "/0/vars_files",
    "keyword": "type",
    "message": "must be object",
    "params": {
      "type": "object"
    },
    "schemaPath": "#/patternProperties/vars/type"
  },
  {
    "instancePath": "/0/vars_files/0",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/vars_files/items/oneOf/0/type"
  },
  {
    "instancePath": "/0/vars_files/0/0",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/vars_files/items/oneOf/1/items/type"
  },
  {
    "instancePath": "/0/vars_files/0/1",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/properties/vars_files/items/oneOf/1/items/type"
  },
  {
    "instancePath": "/0/vars_files/0",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/properties/vars_files/items/oneOf"
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
      "filename": "negative_test/playbooks/var_files_list_of_list_number.yml",
      "path": "$[0]",
      "message": "{'name': 'var_files should not accept array[number]', 'hosts': 'localhost', 'vars_files': [[0, 1]]} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'hosts' does not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "best_deep_match": {
        "path": "$[0].vars_files[0][0]",
        "message": "0 is not of type 'string'"
      },
      "num_sub_errors": 8,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'hosts' does not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "{'name': 'var_files should not accept array[number]', 'hosts': 'localhost', 'vars_files': [[0, 1]]} is not valid under any of the given schemas"
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
          "path": "$[0].vars_files",
          "message": "[[0, 1]] is not of type 'object'"
        },
        {
          "path": "$[0].vars_files[0]",
          "message": "[0, 1] is not valid under any of the given schemas"
        },
        {
          "path": "$[0].vars_files[0]",
          "message": "[0, 1] is not of type 'string'"
        },
        {
          "path": "$[0].vars_files[0][0]",
          "message": "0 is not of type 'string'"
        },
        {
          "path": "$[0].vars_files[0][1]",
          "message": "1 is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
