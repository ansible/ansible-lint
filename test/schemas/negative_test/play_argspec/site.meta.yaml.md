# ajv errors

```json
[
  {
    "instancePath": "/argument_specs/weather_check",
    "keyword": "required",
    "message": "must have required property 'options'",
    "params": {
      "missingProperty": "options"
    },
    "schemaPath": "#/properties/argument_specs/patternProperties/%5E%5Ba-zA-Z_%5D%5Ba-zA-Z0-9_%5D*%24/required"
  },
  {
    "instancePath": "/argument_specs/weather_check",
    "keyword": "required",
    "message": "must have required property 'examples'",
    "params": {
      "missingProperty": "examples"
    },
    "schemaPath": "#/properties/argument_specs/patternProperties/%5E%5Ba-zA-Z_%5D%5Ba-zA-Z0-9_%5D*%24/required"
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
      "filename": "negative_test/play_argspec/site.meta.yaml",
      "path": "$.argument_specs.weather_check",
      "message": "'options' is a required property",
      "has_sub_errors": false
    },
    {
      "filename": "negative_test/play_argspec/site.meta.yaml",
      "path": "$.argument_specs.weather_check",
      "message": "'examples' is a required property",
      "has_sub_errors": false
    }
  ],
  "parse_errors": []
}
```
