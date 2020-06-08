"""Rule definition for a failure to load a file."""

from ansiblelint.rules import AnsibleLintRule


class LoadingFailureRule(AnsibleLintRule):
    """File loading failure."""

    id = '901'
    shortdesc = 'Failed to load or parse file'
    description = 'Linter failed to process a YAML file, possible not an Ansible file.'
    severity = 'VERY_HIGH'
    tags = ['core']
    version_added = 'v4.3.0'
