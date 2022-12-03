"""Utility to generate some complex patterns."""
import copy
import json
import keyword
import sys
from typing import Any

play_keywords = list(
    filter(
        None,
        """\
any_errors_fatal
become
become_exe
become_flags
become_method
become_user
check_mode
collections
connection
debugger
diff
environment
fact_path
force_handlers
gather_facts
gather_subset
gather_timeout
handlers
hosts
ignore_errors
ignore_unreachable
max_fail_percentage
module_defaults
name
no_log
order
port
post_tasks
pre_tasks
remote_user
roles
run_once
serial
strategy
tags
tasks
throttle
timeout
vars
vars_files
vars_prompt
""".split(),
    )
)


def is_ref_used(obj: Any, ref: str) -> bool:
    """Return a reference use from a schema."""
    ref_use = f"#/$defs/{ref}"
    if isinstance(obj, dict):
        if obj.get("$ref", None) == ref_use:
            return True
        for _ in obj.values():
            if isinstance(_, (dict, list)):
                if is_ref_used(_, ref):
                    return True
    elif isinstance(obj, list):
        for _ in obj:
            if isinstance(_, (dict, list)):
                if is_ref_used(_, ref):
                    return True
    return False


if __name__ == "__main__":

    invalid_var_names = sorted(list(keyword.kwlist) + play_keywords)
    if "__peg_parser__" in invalid_var_names:
        invalid_var_names.remove("__peg_parser__")
    print("Updating invalid var names")

    with open("f/vars.json", "r+", encoding="utf-8") as f:
        vars_schema = json.load(f)
        vars_schema["anyOf"][0]["patternProperties"] = {
            f"^(?!({'|'.join(invalid_var_names)})$)[a-zA-Z_][\\w]*$": {}
        }
        f.seek(0)
        json.dump(vars_schema, f, indent=2)
        f.write("\n")
        f.truncate()

    print("Compiling subschemas...")
    with open("f/ansible.json", encoding="utf-8") as f:
        combined_json = json.load(f)

    for subschema in ["tasks", "playbook"]:
        sub_json = copy.deepcopy(combined_json)
        # remove unsafe keys from root
        for key in [
            "$id",
            "id",
            "title",
            "description",
            "type",
            "default",
            "items",
            "properties",
            "additionalProperties",
            "examples",
        ]:
            if key in sub_json:
                del sub_json[key]
        for key in sub_json:
            if key not in ["$schema", "$defs"]:
                print(f"Unexpected key found at combined schema root: ${key}")
                sys.exit(2)
        # Copy keys from subschema to root
        for key, value in combined_json["$defs"][subschema].items():
            sub_json[key] = value
        sub_json["$comment"] = "Generated from ansible.json, do not edit."
        sub_json[
            "$id"
        ] = f"https://raw.githubusercontent.com/ansible-lint/main/src/ansiblelint/schemas/{subschema}.json"

        # Remove all unreferenced ($ref) definitions ($defs) recursively
        while True:
            spare = []
            for k in sub_json["$defs"].keys():
                if not is_ref_used(sub_json, k):
                    spare.append(k)
            for k in spare:
                print(f"{subschema}: deleting unused '{k}' definition")
                del sub_json["$defs"][k]
            if not spare:
                break

        with open(f"f/{subschema}.json", "w", encoding="utf-8") as f:
            json.dump(sub_json, f, indent=2, sort_keys=True)
            f.write("\n")
