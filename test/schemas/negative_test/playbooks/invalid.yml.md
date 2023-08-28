# ajv errors

```json
[
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
    "keyword": "not",
    "message": "must NOT be valid",
    "params": {},
    "schemaPath": "#/allOf/1/not"
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
      "filename": "negative_test/playbooks/invalid.yml",
      "path": "$[0]",
      "message": "{'name': 'foo', 'hosts': 'localhost', 'import_playbook': 'included.yml'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "{'name': 'foo', 'hosts': 'localhost', 'import_playbook': 'included.yml'} should not be valid under {'required': ['import_playbook']}"
      },
      "best_deep_match": {
        "path": "$[0]",
        "message": "'hosts' does not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
      },
      "num_sub_errors": 2,
      "sub_errors": [
        {
          "path": "$[0]",
          "message": "'hosts' does not match any of the regexes: '^(ansible\\\\.builtin\\\\.)?import_playbook$', 'name', 'tags', 'vars', 'when'"
        },
        {
          "path": "$[0]",
          "message": "Additional properties are not allowed ('import_playbook' was unexpected)"
        },
        {
          "path": "$[0]",
          "message": "{'name': 'foo', 'hosts': 'localhost', 'import_playbook': 'included.yml'} should not be valid under {'required': ['import_playbook']}"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
