# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

from ansiblelint.rules import AnsibleLintRule

META_STR_INFO = (
    'author',
    'description'
)
META_INFO = tuple(list(META_STR_INFO) + [
    'license',
    'min_ansible_version',
    'platforms',
])


def _platform_info_errors_itr(platforms):
    if not isinstance(platforms, list):
        yield 'Platforms should be a list of dictionaries'
        return

    for platform in platforms:
        if not isinstance(platform, dict):
            yield 'Platforms should be a list of dictionaries'
        elif 'name' not in platform:
            yield 'Platform should contain name'


def _galaxy_info_errors_itr(galaxy_info,
                            info_list=META_INFO,
                            str_info_list=META_STR_INFO):
    for info in info_list:
        ginfo = galaxy_info.get(info, False)
        if ginfo:
            if info in str_info_list and not isinstance(ginfo, str):
                yield '{info} should be a string'.format(info=info)
            elif info == 'platforms':
                for err in _platform_info_errors_itr(ginfo):
                    yield err
        else:
            yield 'Role info should contain {info}'.format(info=info)


class MetaMainHasInfoRule(AnsibleLintRule):
    id = '701'
    shortdesc = 'meta/main.yml should contain relevant info'
    str_info = META_STR_INFO
    info = META_INFO
    description = (
        'meta/main.yml should contain: ``{}``'.format(', '.join(info))
    )
    severity = 'HIGH'
    tags = ['metadata']
    version_added = 'v4.0.0'

    def matchplay(self, file, data):
        if file['type'] != 'meta':
            return False

        meta = {'meta/main.yml': data}
        galaxy_info = data.get('galaxy_info', False)
        if galaxy_info:
            return [(meta, err) for err
                    in _galaxy_info_errors_itr(galaxy_info)]

        return [(meta, "No 'galaxy_info' found")]
