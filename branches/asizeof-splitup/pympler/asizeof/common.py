


class _NamedRef(object):
    '''Store referred object along
       with the name of the referent.
    '''
    __slots__ = ('name', 'ref')

    def __init__(self, name, ref):
        self.name = name
        self.ref  = ref


class _Slots(tuple):
    '''Wrapper class for __slots__ attribute at
       class instances to account for the size
       of the __slots__ tuple/list containing
       references to the attribute values.
    '''
    pass


def _nameof(obj, dflt=''):
    '''Return the name of an object.
    '''
    return getattr(obj, '__name__', dflt)

def _repr(obj, clip=80):
    '''Clip long repr() string.
    '''
    try:  # safe repr()
        r = repr(obj)
    except TypeError:
        r = 'N/A'
    if 0 < clip < len(r):
        h = (clip // 2) - 2
        if h > 0:
            r = r[:h] + '....' + r[-h:]
    return r
