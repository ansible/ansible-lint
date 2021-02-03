"""Store configuration options as a singleton."""
from argparse import Namespace

DEFAULT_KINDS = [
  # Do not sort this list, order matters.
  {"requirements": "requirements.yml"},  # v2 and v1
  {"requirements": "**/meta/requirements.yml"},  # v1 only
  {"reno": "releasenotes/*/*.{yaml,yml}"},  # reno release notes
  {"playbook": "**/playbooks/*.{yml,yaml}"},
  {"playbook": "**/*playbook*.{yml,yaml}"},
  {"role": "**/roles/*/"},
  {"tasks": "**/tasks/*.{yaml,yml}"},
  {"handlers": "**/handlers/*.{yaml,yml}"},
  {"vars": "**/{vars,defaults}/*.{yaml,yml}"},
  {"meta": "**/meta/main.{yaml,yml}"},
  {"yaml": ".config/molecule/config.{yaml,yml}"},  # molecule global config
  {"yaml": "**/molecule/*/molecule.{yaml,yml}"},  # molecule config
  {"playbook": "**/molecule/*/*.{yaml,yml}"},  # molecule playbooks
  {"yaml": "**/*.{yaml,yml}"},
  {"yaml": "**/.*.{yaml,yml}"},
]

options = Namespace(
    colored=True,
    cwd=".",
    display_relative_path=True,
    exclude_paths=[],
    lintables=[],
    listrules=False,
    listtags=False,
    parseable=False,
    parseable_severity=False,
    quiet=False,
    rulesdirs=[],
    skip_list=[],
    tags=[],
    verbosity=False,
    warn_list=[],
    kinds=DEFAULT_KINDS,
    mock_modules=[],
    mock_roles=[]
)
