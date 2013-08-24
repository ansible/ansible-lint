class Formatter:
    
    def format(self, match):
        formatstr = "[{}] {}\n{}:{}\n{}\n"
        return formatstr.format(match.rule.id,
                                match.rule.description,
                                match.filename, 
                                match.linenumber,
                                match.line)

class QuietFormatter:

    def format(self, match):
        formatstr = "[{}] {}:{}"
        return formatstr.format(match.rule.id, match.filename, 
                                match.linenumber)
