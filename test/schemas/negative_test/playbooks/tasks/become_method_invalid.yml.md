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
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/anyOf/0/type"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "ansible.builtin.sudo",
        "ansible.builtin.su",
        "community.general.pbrun",
        "community.general.pfexec",
        "ansible.builtin.runas",
        "community.general.dzdo",
        "community.general.ksu",
        "community.general.doas",
        "community.general.machinectl",
        "community.general.pmrun",
        "community.general.sesu",
        "community.general.sudosu"
      ]
    },
    "schemaPath": "#/anyOf/0/enum"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/anyOf/2/type"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/anyOf"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/anyOf/0/type"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "enum",
    "message": "must be equal to one of the allowed values",
    "params": {
      "allowedValues": [
        "ansible.builtin.sudo",
        "ansible.builtin.su",
        "community.general.pbrun",
        "community.general.pfexec",
        "ansible.builtin.runas",
        "community.general.dzdo",
        "community.general.ksu",
        "community.general.doas",
        "community.general.machinectl",
        "community.general.pmrun",
        "community.general.sesu",
        "community.general.sudosu"
      ]
    },
    "schemaPath": "#/anyOf/0/enum"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/$defs/full-jinja/type"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/anyOf/2/type"
  },
  {
    "instancePath": "/0/become_method",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/anyOf"
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
  "successes": [],
  "errors": [
    {
      "filename": "negative_test/playbooks/tasks/become_method_invalid.yml",
      "path": "$[0]",
      "message": "{'command': 'echo 123', 'vars': {'sudo_var': 'doo'}, 'become_method': True} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$[0]",
        "message": "'block' is a required property"
      },
      "best_deep_match": {
        "path": "$[0].become_method",
        "message": "True is not one of ['ansible.builtin.sudo', 'ansible.builtin.su', 'community.general.pbrun', 'community.general.pfexec', 'ansible.builtin.runas', 'community.general.dzdo', 'community.general.ksu', 'community.general.doas', 'community.general.machinectl', 'community.general.pmrun', 'community.general.sesu', 'community.general.sudosu']"
      },
      "num_sub_errors": 10,
      "sub_errors": [
        {
          "path": "$[0].become_method",
          "message": "True is not valid under any of the given schemas"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not one of ['ansible.builtin.sudo', 'ansible.builtin.su', 'community.general.pbrun', 'community.general.pfexec', 'ansible.builtin.runas', 'community.general.dzdo', 'community.general.ksu', 'community.general.doas', 'community.general.machinectl', 'community.general.pmrun', 'community.general.sesu', 'community.general.sudosu']"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not of type 'string'"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not of type 'string'"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not of type 'string'"
        },
        {
          "path": "$[0]",
          "message": "'block' is a required property"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not valid under any of the given schemas"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not one of ['ansible.builtin.sudo', 'ansible.builtin.su', 'community.general.pbrun', 'community.general.pfexec', 'ansible.builtin.runas', 'community.general.dzdo', 'community.general.ksu', 'community.general.doas', 'community.general.machinectl', 'community.general.pmrun', 'community.general.sesu', 'community.general.sudosu']"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not of type 'string'"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not of type 'string'"
        },
        {
          "path": "$[0].become_method",
          "message": "True is not of type 'string'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
