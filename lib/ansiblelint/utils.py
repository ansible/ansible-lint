def matchlines(text, fn):
    result = []
    # arrays are 0-based, line numbers are 1-based
    # so use prev_line_no as the counter 
    for (prev_line_no, line) in enumerate(text.split("\n")):
        if fn(line):
            result.append(prev_line_no+1)
    return result
