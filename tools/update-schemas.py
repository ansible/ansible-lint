"""Rebuilds JSON Schemas from our models."""
import json
import subprocess
import sys


VSCODE_SETTINGS = """
  "yaml.schemas": {
    "https://raw.githubusercontent.com/ansible-community/ansible-lint/schemas/src/ansiblelint/data/ansible-requirements-schema.json": ["requirements.yml"],
    "https://raw.githubusercontent.com/ansible-community/ansible-lint/schemas/src/ansiblelint/data/ansible-meta-schema.json": ["meta/main.yml"],
    "https://raw.githubusercontent.com/ansible-community/ansible-lint/schemas/src/ansiblelint/data/ansible-vars-schema.json": ["vars/*.yml", "defaults/*.yml", "host_vars/*.yml", "group_vars/*.yml"],
  },
    "https://raw.githubusercontent.com/ansible-community/ansible-lint/schemas/src/ansiblelint/data/ansible-tasks-schema.json": ["tasks/*.yml", "handlers/*.yml"],
  },
    "https://raw.githubusercontent.com/ansible-community/ansible-lint/schemas/src/ansiblelint/data/ansible-playbook-schema.json": ["playbooks/*.yml"],
  },
"""

if __name__ == "__main__":

    print("Dumping list of Ansible modules")
    #  lazy doc command dumps modules in random order...
    result = subprocess.run(
        "ansible-doc -j -l",
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL  # dump garbage warnings
    )
    modules = sorted(json.loads(result.stdout).keys())
    with open("src/ansiblelint/schemas/_modules.py", "w") as f:
        f.write("ANSIBLE_MODULES = %s\n" % modules)

    for schema in ["requirements", "meta", "vars", "tasks", "playbook"]:
        print(f"Building schema for {schema}")
        subprocess.run(
            [sys.executable, f"src/ansiblelint/schemas/{schema}.py"], check=True
        )

# TODO: validate built schemas, so we do not generate garbage
