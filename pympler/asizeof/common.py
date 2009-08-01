import sizes

 # any classes or types in modules listed in _builtin_modules are
 # considered built-in and ignored by default, as built-in functions
if __name__ == '__main__':
    _builtin_modules = (int.__module__, 'types', Exception.__module__)  # , 'weakref'
else:  # treat this very module as built-in
    _builtin_modules = (int.__module__, 'types', Exception.__module__, __name__)  # , 'weakref'

 # some flags from .../Include/object.h
_Py_TPFLAGS_HEAPTYPE = 1 <<  9  # Py_TPFLAGS_HEAPTYPE
_Py_TPFLAGS_HAVE_GC  = 1 << 14  # Py_TPFLAGS_HAVE_GC

_Type_type = type(type)  # == type and new-style class type




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


def _basicsize(t, base=0, heap=False, obj=None):
    '''Get non-zero basicsize of type,
       including the header sizes.
    '''
    s = max(getattr(t, '__basicsize__', 0), base)
     # include gc header size
    if t != _Type_type:
       h = getattr(t,   '__flags__', 0) & _Py_TPFLAGS_HAVE_GC
    elif heap:  # type, allocated on heap
       h = True
    else:  # None has no __flags__ attr
       h = getattr(obj, '__flags__', 0) & _Py_TPFLAGS_HEAPTYPE
    if h:
       s += sizes._sizeof_CPyGC_Head
     # include reference counters
    return s + sizes._sizeof_Crefcounts

def _itemsize(t, item=0):
    '''Get non-zero itemsize of type.
    '''
     # replace zero value with default
    return getattr(t, '__itemsize__', 0) or item

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
