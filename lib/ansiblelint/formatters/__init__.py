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
                                    color.stringc(str(match.line), 'purple'))
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
                                    color.stringc(match.message, 'red'))
        else:
            return formatstr.format(match.filename,
                                    match.linenumber,
                                    "E" + match.rule.id,
                                    match.message)
