# ajv errors

```json
[
  {
    "instancePath": "/0",
    "keyword": "not",
    "message": "must NOT be valid",
    "params": {},
    "schemaPath": "#/oneOf/0/not"
  },
  {
    "instancePath": "/0",
    "keyword": "not",
    "message": "must NOT be valid",
    "params": {},
    "schemaPath": "#/oneOf/1/not"
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
    "keyword": "not",
    "message": "must NOT be valid",
    "params": {},
    "schemaPath": "#/allOf/0/not"
  },
  {
    "instancePath": "/0",
    "keyword": "not",
    "message": "must NOT be valid",
    "params": {},
    "schemaPath": "#/allOf/1/not"
  },
  {
    "instancePath": "/0",
    "keyword": "required",
    "message": "must have required property 'hosts'",
    "params": {
      "missingProperty": "hosts"
    },
    "schemaPath": "#/required"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "ansible.builtin.import_playbook"
    },
    "schemaPath": "#/additionalProperties"
  },
  {
    "instancePath": "/0",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "import_playbook"
    },
    "schemaPath": "#/additionalProperties"
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
      "filename": "negative_test/playbooks/import_playbook_exclusive.yml",
      "path": "$[0]",
      "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} should not be valid under {'required': ['ansible.builtin.import_playbook']}"
      },
      "best_deep_match": {
        "path": "$[0]",
        "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} should not be valid under {'required': ['import_playbook']}"
      },
      "num_sub_errors": 6,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} is not valid under any of the given schemas"
        },
        {
          "path": "$[0]",
          "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} should not be valid under {'required': ['import_playbook']}"
        },
        {
          "path": "$[0]",
          "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} should not be valid under {'required': ['ansible.builtin.import_playbook']}"
        },
        {
          "path": "$[0]",
          "message": "Additional properties are not allowed ('ansible.builtin.import_playbook', 'import_playbook' were unexpected)"
        },
        {
          "path": "$[0]",
          "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} should not be valid under {'required': ['ansible.builtin.import_playbook']}"
        },
        {
          "path": "$[0]",
          "message": "{'ansible.builtin.import_playbook': 'foo.yml', 'import_playbook': 'other.yml'} should not be valid under {'required': ['import_playbook']}"
        },
        {
          "path": "$[0]",
          "message": "'hosts' is a required property"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
