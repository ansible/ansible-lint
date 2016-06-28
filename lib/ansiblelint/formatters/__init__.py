class Formatter(object):

    def format(self, match):
        formatstr = u"[{0}] {1}\n{2}:{3}\n{4}\n"
        return formatstr.format(match.rule.id,
                                match.message,
                                match.filename,
                                match.linenumber,
                                match.line)


class QuietFormatter(object):

    def format(self, match):
        formatstr = u"[{0}] {1}:{2}"
        return formatstr.format(match.rule.id, match.filename,
                                match.linenumber)


class ParseableFormatter(object):

    def format(self, match):
        formatstr = u"{0}:{1}: [{2}] {3}"
        return formatstr.format(match.filename,
                                match.linenumber,
                                "E" + match.rule.id,
                                match.message,
                                )


from ansiblelint.utils import stringc

class ColoredFormatter(object):

    def format(self, match):
        formatstr = u"{0} {1}\n{2}:{3}\n{4}\n"
        return formatstr.format(stringc(u"[{0}]".format(match.rule.id), 'bright red'),
                                stringc(match.message, 'red'),
                                stringc(match.filename, 'blue'),
                                stringc(match.linenumber, 'cyan'),
                                stringc(match.line, 'magenta')
                                )