# ajv errors

```json
[
  {
    "instancePath": "/0",
    "keyword": "required",
    "message": "must have required property 'block'",
    "params": {
      "missingProperty": "block"
    },
    "schemaPath": "#/required"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "sudo",
        "su",
        "pbrun",
        "pfexec",
        "runas",
        "dzdo",
        "ksu",
        "doas",
        "machinectl",
        "pmrun",
        "sesu",
        "sudosu"
      ]
    },
    "schemaPath": "#/oneOf/0/enum"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "pattern",
    "message": "must match pattern \"^\\{[\\{%](.|[\r\n])*[\\}%]\\}$\"",
    "params": {
      "pattern": "^\\{[\\{%](.|[\r\n])*[\\}%]\\}$"
    },
    "schemaPath": "#/$defs/full-jinja/pattern"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "pattern",
    "message": "must match pattern \"^[A-Z][a-z][0-9]._$\"",
    "params": {
      "pattern": "^[A-Z][a-z][0-9]._$"
    },
    "schemaPath": "#/oneOf/2/pattern"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "sudo",
        "su",
        "pbrun",
        "pfexec",
        "runas",
        "dzdo",
        "ksu",
        "doas",
        "machinectl",
        "pmrun",
        "sesu",
        "sudosu"
      ]
    },
    "schemaPath": "#/oneOf/0/enum"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "pattern",
    "message": "must match pattern \"^\\{[\\{%](.|[\r\n])*[\\}%]\\}$\"",
    "params": {
      "pattern": "^\\{[\\{%](.|[\r\n])*[\\}%]\\}$"
    },
    "schemaPath": "#/$defs/full-jinja/pattern"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "pattern",
    "message": "must match pattern \"^[A-Z][a-z][0-9]._$\"",
    "params": {
      "pattern": "^[A-Z][a-z][0-9]._$"
    },
    "schemaPath": "#/oneOf/2/pattern"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "oneOf",
    "message": "must match exactly one schema in oneOf",
    "params": {
      "passingSchemas": null
    },
    "schemaPath": "#/oneOf"
  },
  {
    "instancePath": "/0",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/items/anyOf"
  }
]
```

# check-jsonschema

stdout:

```json
{
  "status": "fail",
  "errors": [
    {
      "filename": "negative_test/playbooks/tasks/become_method_untemplated.yml",
      "path": "$[0]",
      "message": "{'command': 'echo 123', 'vars': {'sudo_var': 'doo'}, 'become_method': 'sudo_var'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "sub_errors": [
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' is not one of ['sudo', 'su', 'pbrun', 'pfexec', 'runas', 'dzdo', 'ksu', 'doas', 'machinectl', 'pmrun', 'sesu', 'sudosu']"
        },
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
        },
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' does not match '^[A-Z][a-z][0-9]._$'"
        },
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' is not valid under any of the given schemas"
        },
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' is not one of ['sudo', 'su', 'pbrun', 'pfexec', 'runas', 'dzdo', 'ksu', 'doas', 'machinectl', 'pmrun', 'sesu', 'sudosu']"
        },
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' does not match '^\\\\{[\\\\{%](.|[\\r\\n])*[\\\\}%]\\\\}$'"
        },
        {
          "path": "$[0].become_method",
          "message": "'sudo_var' does not match '^[A-Z][a-z][0-9]._$'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
