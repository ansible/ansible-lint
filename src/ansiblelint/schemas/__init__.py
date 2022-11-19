"""Module containing cached JSON schemas."""
import logging
import os
import sys
import urllib.request

_logger = logging.getLogger(__package__)


# Maps kinds to JSON schemas
# See https://www.schemastore.org/json/
JSON_SCHEMAS = {
    # Do not use anchors in these URLs because python-jsonschema does not support them:
    "playbook": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-playbook.json",
    "tasks": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-tasks.json",
    "vars": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-vars.json",
    "requirements": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-requirements.json",
    "meta": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-meta.json",
    "galaxy": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-galaxy.json",
    "execution-environment": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-ee.json",
    "meta-runtime": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-meta-runtime.json",
    "inventory": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-inventory.json",
    "ansible-lint-config": "https://raw.githubusercontent.com/ansible/ansible-lint/main/src/ansiblelint/schemas/ansible-lint-config.json",
    "ansible-navigator-config": "https://raw.githubusercontent.com/ansible/ansible-navigator/main/src/ansible_navigator/data/ansible-navigator.json",
    "arg_specs": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-argument-specs.json",
}


def refresh_schemas() -> int:
    """Refresh JSON schemas by downloading latest versions.

    Returns number of changed schemas.
    """
    changed = 0
    for kind, url in sorted(JSON_SCHEMAS.items()):
        if url.startswith("https://raw.githubusercontent.com/ansible/ansible-lint"):
            _logger.warning(
                "Skipped updating schema that is part of the ansible-lint repository: %s",
                url,
            )
            continue
        path = f"{os.path.relpath(os.path.dirname(__file__))}/{kind}.json"
        print(f"Refreshing {path} ...")
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
            with open(f"{path}", "r+", encoding="utf-8") as f_out:
                if f_out.read() != content:
                    f_out.seek(0)
                    f_out.write(content)
                    f_out.truncate()
                    changed += 1
    return changed


if __name__ == "__main__":

    if refresh_schemas():
        print(
            "Schemas are outdated, please update them in a separate pull request.",
        )
        sys.exit(1)
    else:
        print("Schemas already updated", 0)
