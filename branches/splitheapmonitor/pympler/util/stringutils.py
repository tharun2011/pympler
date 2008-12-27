
def trunc(s, max, left=0):
    """
    Convert 's' to string, eliminate newlines and truncate the string to 'max'
    characters. If there are more characters in the string add '...' to the
    string. With 'left=1', the string can be truncated at the beginning.
    """
    s = str(s)
    s = s.replace('\n', '|')
    if len(s) > max:
        if left:
            return '...'+s[len(s)-max+3:]
        else:
            return s[:(max-3)]+'...'
    else:
        return s

def pp(i, base=1024):
    """
    Pretty-print the integer `i` as a human-readable size representation.
    """
    degree = 0
    pattern = "%4d     %s"
    while i > base:
        pattern = "%7.2f %s"
        i = i / float(base)
        degree += 1
    scales = ['B', 'KB', 'MB', 'GB', 'TB', 'EB']
    return pattern % (i, scales[degree])

