# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import six

from ansiblelint import AnsibleLintRule


class MetaMainHasInfoRule(AnsibleLintRule):
    id = '701'
    shortdesc = 'meta/main.yml should contain relevant info'
    info = [
        'author',
        'description',
        'license',
        'min_ansible_version',
        'platforms',
    ]
    description = (
        'meta/main.yml should contain: ``{}``'.format(', '.join(info))
    )
    severity = 'HIGH'
    tags = ['metadata']
    version_added = 'v4.0.0'

    def matchplay(self, file, data):
        if file['type'] != 'meta':
            return False

        galaxy_info = data.get('galaxy_info', None)
        if not galaxy_info:
            return [({'meta/main.yml': data},
                    "No 'galaxy_info' found")]

        results = []
        for info in self.info:
            if not galaxy_info.get(info, None):
                results.append(({'meta/main.yml': data},
                                'Role info should contain %s' % info))

        for info in ['author', 'description']:
            if not galaxy_info.get(info):
                continue
            if not isinstance(galaxy_info.get(info), six.string_types):
                results.append(({'meta/main.yml': data},
                                '%s should be a string' % info))

        platforms = galaxy_info.get('platforms', None)
        if not platforms:
            return results

        if not isinstance(platforms, list):
            results.append(({'meta/main.yml': data},
                            'Platforms should be a list of dictionaries'))
            return results

        for platform in platforms:
            if not isinstance(platform, dict):
                results.append(({'meta/main.yml': data},
                                'Platforms should be a list of dictionaries'))
                continue
            if not platform.get('name', None):
                results.append(({'meta/main.yml': data},
                                'Platform should contain name'))

        return results
