# Copyright (c) 2018, Ansible Project

from typing import TYPE_CHECKING, List

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class MetaChangeFromDefaultRule(AnsibleLintRule):
    id = 'meta-incorrect'
    shortdesc = 'meta/main.yml default values should be changed'
    field_defaults = [
        ('author', 'your name'),
        ('description', 'your description'),
        ('company', 'your company (optional)'),
        ('license', 'license (GPLv2, CC-BY, etc)'),
        ('license', 'license (GPL-2.0-or-later, MIT, etc)'),
    ]
    description = 'meta/main.yml default values should be changed for: ``{}``'.format(
        ', '.join(f[0] for f in field_defaults)
    )
    severity = 'HIGH'
    tags = ['metadata']
    version_added = 'v4.0.0'

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        if file.kind != 'meta':
            return []

        galaxy_info = data.get('galaxy_info', None)
        if not galaxy_info:
            return []

        results = []
        for field, default in self.field_defaults:
            value = galaxy_info.get(field, None)
            if value and value == default:
                results.append(
                    self.create_matcherror(
                        filename=file,
                        linenumber=data['__line__'],
                        message='Should change default metadata: %s' % field,
                    )
                )

        return results
