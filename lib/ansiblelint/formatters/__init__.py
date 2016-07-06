try:
    from ansible.color import stringc
except ImportError:
    from ansible.utils.color import stringc


class Formatter(object):

    def format(self, match, colored=False):
        formatstr = u"{0} {1}\n{2}:{3}\n{4}\n"
        if colored:
            return formatstr.format(stringc(u"[{0}]".format(match.rule.id), 'bright red'),
                                    stringc(match.message, 'red'),
                                    stringc(match.filename, 'blue'),
                                    stringc(match.linenumber, 'cyan'),
                                    stringc(match.line, 'purple'))
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
            return formatstr.format(stringc(u"[{0}]".format(match.rule.id), 'bright red'),
                                    stringc(match.filename, 'blue'),
                                    stringc(match.linenumber, 'cyan'))
        else:
            return formatstr.format(match.rule.id, match.filename,
                                    match.linenumber)


class ParseableFormatter(object):

    def format(self, match, colored=False):
        formatstr = u"{0}:{1}: [{2}] {3}"
        if colored:
            return formatstr.format(stringc(match.filename, 'blue'),
                                    stringc(match.linenumber, 'cyan'),
                                    stringc(u"E{0}".format(match.rule.id), 'bright red'),
                                    stringc(match.message, 'red'))
        else:
            return formatstr.format(match.filename,
                                    match.linenumber,
                                    "E" + match.rule.id,
                                    match.message)
