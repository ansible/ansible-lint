try:
    from ansible import color
except ImportError:
    from ansible.utils import color


class Formatter(object):

    def format(self, match, colored=False):
        formatstr = u"{0} {1}\n{2}:{3}\n{4}\n"
        if colored:
            color.ANSIBLE_COLOR = True
            return formatstr.format(color.stringc(u"[{0}]".format(match.rule.id), 'bright red'),
                                    color.stringc(match.message, 'red'),
                                    color.stringc(match.filename, 'blue'),
                                    color.stringc(str(match.linenumber), 'cyan'),
                                    color.stringc(u"{0}".format(match.line), 'purple'))
        else:
            return formatstr.format(match.rule.id,
                                    match.message,
                                    match.filename,
                                    match.linenumber,
                                    match.line)


class QuietFormatter(object):

    def format(self, match, colored=False):
        formatstr = u"{0} {1}:{2}"
        if colored:
            color.ANSIBLE_COLOR = True
            return formatstr.format(color.stringc(u"[{0}]".format(match.rule.id), 'bright red'),
                                    color.stringc(match.filename, 'blue'),
                                    color.stringc(str(match.linenumber), 'cyan'))
        else:
            return formatstr.format(match.rule.id, match.filename,
                                    match.linenumber)


class ParseableFormatter(object):

    def format(self, match, colored=False):
        formatstr = u"{0}:{1}: [{2}] {3}"
        if colored:
            color.ANSIBLE_COLOR = True
            return formatstr.format(color.stringc(match.filename, 'blue'),
                                    color.stringc(str(match.linenumber), 'cyan'),
                                    color.stringc(u"E{0}".format(match.rule.id), 'bright red'),
                                    color.stringc(u"{0}".format(match.message), 'red'))
        else:
            return formatstr.format(match.filename,
                                    match.linenumber,
                                    "E" + match.rule.id,
                                    match.message)


class ParseableSeverityFormatter(object):

    def format(self, match, colored=False):
        formatstr = u"{0}:{1}: [{2}] [{3}] {4}"

        filename = match.filename
        linenumber = str(match.linenumber)
        rule_id = u"E{0}".format(match.rule.id)
        severity = match.rule.severity
        message = str(match.message)

        if colored:
            color.ANSIBLE_COLOR = True
            filename = color.stringc(filename, 'blue')
            linenumber = color.stringc(linenumber, 'cyan')
            rule_id = color.stringc(rule_id, 'bright red')
            severity = color.stringc(severity, 'bright red')
            message = color.stringc(message, 'red')

        return formatstr.format(
            filename,
            linenumber,
            rule_id,
            severity,
            message,
        )
