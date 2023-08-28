# ajv errors

```json
[
  {
    "instancePath": "",
    "keyword": "additionalProperties",
    "message": "must NOT have additional properties",
    "params": {
      "additionalProperty": "12"
    },
    "schemaPath": "#/anyOf/0/additionalProperties"
  },
  {
    "instancePath": "",
    "keyword": "type",
    "message": "must be string",
    "params": {
      "type": "string"
    },
    "schemaPath": "#/anyOf/1/type"
  },
  {
    "instancePath": "",
    "keyword": "type",
    "message": "must be null",
    "params": {
      "type": "null"
    },
    "schemaPath": "#/anyOf/2/type"
  },
  {
    "instancePath": "",
    "keyword": "anyOf",
    "message": "must match a schema in anyOf",
    "params": {},
    "schemaPath": "#/anyOf"
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
      "filename": "negative_test/playbooks/vars/numeric-var-name.yml",
      "path": "$",
      "message": "{'12': '...'} is not valid under any of the given schemas",
      "has_sub_errors": true,
      "best_match": {
        "path": "$",
        "message": "{'12': '...'} is not of type 'string'"
      },
      "best_deep_match": {
        "path": "$",
        "message": "'12' does not match any of the regexes: '^(?!(False|None|True|and|any_errors_fatal|as|assert|async|await|become|become_exe|become_flags|become_method|become_user|break|check_mode|class|collections|connection|continue|debugger|def|del|diff|elif|else|environment|except|fact_path|finally|for|force_handlers|from|gather_facts|gather_subset|gather_timeout|global|handlers|hosts|if|ignore_errors|ignore_unreachable|import|in|is|lambda|max_fail_percentage|module_defaults|name|no_log|nonlocal|not|or|order|pass|port|post_tasks|pre_tasks|raise|remote_user|return|roles|run_once|serial|strategy|tags|tasks|throttle|timeout|try|vars|vars_files|vars_prompt|while|with|yield)$)[a-zA-Z_][\\\\w]*$'"
      },
      "num_sub_errors": 2,
      "sub_errors": [
        {
          "path": "$",
          "message": "'12' does not match any of the regexes: '^(?!(False|None|True|and|any_errors_fatal|as|assert|async|await|become|become_exe|become_flags|become_method|become_user|break|check_mode|class|collections|connection|continue|debugger|def|del|diff|elif|else|environment|except|fact_path|finally|for|force_handlers|from|gather_facts|gather_subset|gather_timeout|global|handlers|hosts|if|ignore_errors|ignore_unreachable|import|in|is|lambda|max_fail_percentage|module_defaults|name|no_log|nonlocal|not|or|order|pass|port|post_tasks|pre_tasks|raise|remote_user|return|roles|run_once|serial|strategy|tags|tasks|throttle|timeout|try|vars|vars_files|vars_prompt|while|with|yield)$)[a-zA-Z_][\\\\w]*$'"
        },
        {
          "path": "$",
          "message": "{'12': '...'} is not of type 'string'"
        },
        {
          "path": "$",
          "message": "{'12': '...'} is not of type 'null'"
        }
      ]
    }
  ],
  "parse_errors": []
}
```
