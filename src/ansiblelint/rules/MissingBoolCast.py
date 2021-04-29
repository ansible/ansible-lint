from ansiblelint import AnsibleLintRule

import re

# we match anything that has '| default(<bool>)'
contains_default_bool_re = r'.*\|default\((\'?)(true|false|yes|no)(\'?)\)'
condition_contains_bool_default = re.compile(contains_default_bool_re, re.IGNORECASE)

# and we check that anything that matches contains a '| bool' immediately after the match
condition_contains_bool_cast = re.compile(contains_default_bool_re + r'\|bool', re.IGNORECASE)

class MissingBoolCast(AnsibleLintRule):
    id = 'BOOLFILTER405'
    shortdesc = 'Missing |bool in `when:` condition with a `default(<boolean>)`'
    description = '''
    This filter checks that any jinja or expression in the code that uses a boolean default is correctly
    postpended by "| bool".

    This is an issue because any non "boolean" value will be truthy.
    For instance: `{{ x | default(false) }}` will be 'true' if `x = 'no'`!
    '''
    tags = ['idiom']
    severity = 'HIGH'

    def match(self, info, line):
        return is_bool_filter_missing(line)

def is_bool_filter_missing(string):
    normalized_string = string.replace(' ', '') # remove all spaces to simplify regex match
    contains_bool_default = condition_contains_bool_default.match(normalized_string)
    if contains_bool_default:
        return not condition_contains_bool_cast.match(normalized_string)
    return False
