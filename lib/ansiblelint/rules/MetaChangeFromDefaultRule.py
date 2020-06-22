# Copyright (c) 2018, Ansible Project

from ansiblelint.rules import AnsibleLintRule


class MetaChangeFromDefaultRule(AnsibleLintRule):
    id = '703'
    shortdesc = 'meta/main.yml default values should be changed'
    field_defaults = [
        ('author', 'your name'),
        ('description', 'your description'),
        ('company', 'your company (optional)'),
        ('license', 'license (GPLv2, CC-BY, etc)'),
        ('license', 'license (GPL-2.0-or-later, MIT, etc)'),
    ]
    description = (
        'meta/main.yml default values should be changed for: ``{}``'.format(
            ', '.join(f[0] for f in field_defaults)
        )
    )
    severity = 'HIGH'
    tags = ['metadata']
    version_added = 'v4.0.0'

    def matchplay(self, file, data):
        if file['type'] != 'meta':
            return False

        galaxy_info = data.get('galaxy_info', None)
        if not galaxy_info:
            return False

        results = []
        for field, default in self.field_defaults:
            value = galaxy_info.get(field, None)
            if value and value == default:
                results.append(({'meta/main.yml': data},
                                'Should change default metadata: %s' % field))

        return results
