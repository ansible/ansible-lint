def matchlines(text, fn):
    result = []
    for (lineno, line) in enumerate(text.split("\n")):
        if fn(line):
            result.append(lineno)
    return result
