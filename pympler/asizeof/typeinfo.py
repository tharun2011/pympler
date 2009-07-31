 # type-specific referent functions

from math       import log

import common
import compat
import sizes

def _dir2(obj, pref='', excl=(), slots=None, itor=''):
    '''Return an attribute name, object 2-tuple for certain
       attributes or for the ``__slots__`` attributes of the
       given object, but not both.  Any iterator referent
       objects are returned with the given name if the
       latter is non-empty.
    '''
    if slots:  # __slots__ attrs
        if hasattr(obj, slots):
             # collect all inherited __slots__ attrs
             # from list, tuple, or dict __slots__,
             # while removing any duplicate attrs
            s = {}
            for c in type(obj).mro():
                for a in getattr(c, slots, ()):
                    if hasattr(obj, a):
                        s.setdefault(a, getattr(obj, a))
             # assume __slots__ tuple/list
             # is holding the attr values
            yield slots, common._Slots(s)  # compat._keys(s)
            for t in compat._items(s):
                yield t  # attr name, value
    elif itor:  # iterator referents
        for o in obj:  # iter(obj)
            yield itor, o
    else:  # regular attrs
        for a in dir(obj):
            if a.startswith(pref) and a not in excl and hasattr(obj, a):
               yield a, getattr(obj, a)

def _refs(obj, named, *ats, **kwds):
    '''Return specific attribute objects of an object.
    '''
    if named:
        for a in ats:  # cf. inspect.getmembers()
            if hasattr(obj, a):
                yield common._NamedRef(a, getattr(obj, a))
        if kwds:  # kwds are _dir2() args
            for a, o in _dir2(obj, **kwds):
                yield common._NamedRef(a, o)
    else:
        for a in ats:  # cf. inspect.getmembers()
            if hasattr(obj, a):
                yield getattr(obj, a)
        if kwds:  # kwds are _dir2() args
            for _, o in _dir2(obj, **kwds):
                yield o

def _power2(n):
    '''Find the next power of 2.
    '''
    p2 = 16
    while n > p2:
        p2 += p2
    return p2


def _class_refs(obj, named):
    '''Return specific referents of a class object.
    '''
    return _refs(obj, named, '__class__', '__dict__',  '__doc__', '__mro__',
                             '__name__',  '__slots__', '__weakref__')

def _co_refs(obj, named):
    '''Return specific referents of a code object.
    '''
    return _refs(obj, named, pref='co_')

def _dict_refs(obj, named):
    '''Return key and value objects of a dict/proxy.
    '''
    if named:
        for k, v in compat._items(obj):
            s = str(k)
            yield common._NamedRef('[K] ' + s, k)
            yield common._NamedRef('[V] ' + s + ': ' + common._repr(v), v)
    else:
        for k, v in compat._items(obj):
            yield k
            yield v

def _enum_refs(obj, named):
    '''Return specific referents of an enumerate object.
    '''
    return _refs(obj, named, '__doc__')

def _exc_refs(obj, named):
    '''Return specific referents of an Exception object.
    '''
     # .message raises DeprecationWarning in Python 2.6
    return _refs(obj, named, 'args', 'filename', 'lineno', 'msg', 'text')  # , 'message', 'mixed'

def _file_refs(obj, named):
    '''Return specific referents of a file object.
    '''
    return _refs(obj, named, 'mode', 'name')

def _frame_refs(obj, named):
    '''Return specific referents of a frame object.
    '''
    return _refs(obj, named, pref='f_')

def _func_refs(obj, named):
    '''Return specific referents of a function or lambda object.
    '''
    return _refs(obj, named, '__doc__', '__name__', '__code__',
                             pref='func_', excl=('func_globals',))

def _gen_refs(obj, named):
    '''Return the referent(s) of a generator object.
    '''
     # only some gi_frame attrs
    f = getattr(obj, 'gi_frame', None)
    return _refs(f, named, 'f_locals', 'f_code')

def _im_refs(obj, named):
    '''Return specific referents of a method object.
    '''
    return _refs(obj, named, '__doc__', '__name__', '__code__', pref='im_')

def _inst_refs(obj, named):
    '''Return specific referents of a class instance.
    '''
    return _refs(obj, named, '__dict__', '__class__', slots='__slots__')

def _iter_refs(obj, named):
    '''Return the referent(s) of an iterator object.
    '''
    r = compat._getreferents(obj)  # special case
    return _refs(r, named, itor=common._nameof(obj) or 'iteref')

def _module_refs(obj, named):
    '''Return specific referents of a module object.
    '''
     # ignore this very module
    if obj.__name__ == __name__:
        return ()
     # module is essentially a dict
    return _dict_refs(obj.__dict__, named)

def _prop_refs(obj, named):
    '''Return specific referents of a property object.
    '''
    return _refs(obj, named, '__doc__', pref='f')

def _seq_refs(obj, unused):  # named unused for PyChecker
    '''Return specific referents of a frozen/set, list, tuple and xrange object.
    '''
    return obj  # XXX for r in obj: yield r

def _stat_refs(obj, named):
    '''Return referents of a os.stat object.
    '''
    return _refs(obj, named, pref='st_')

def _statvfs_refs(obj, named):
    '''Return referents of a os.statvfs object.
    '''
    return _refs(obj, named, pref='f_')

def _tb_refs(obj, named):
    '''Return specific referents of a traceback object.
    '''
    return _refs(obj, named, pref='tb_')

def _type_refs(obj, named):
    '''Return specific referents of a type object.
    '''
    return _refs(obj, named, '__dict__', '__doc__', '__mro__',
                             '__name__', '__slots__', '__weakref__')

def _weak_refs(obj, unused):  # named unused for PyChecker
    '''Return weakly referent object.
    '''
    try:  # ignore 'key' of KeyedRef
        return (obj(),)
    except:  # XXX ReferenceError
        return ()  #PYCHOK OK

_all_refs = (None, _class_refs,   _co_refs,   _dict_refs,  _enum_refs,
                   _exc_refs,     _file_refs, _frame_refs, _func_refs,
                   _gen_refs,     _im_refs,   _inst_refs,  _iter_refs,
                   _module_refs,  _prop_refs, _seq_refs,   _stat_refs,
                   _statvfs_refs, _tb_refs,   _type_refs,  _weak_refs)


 # type-specific length functions

def _len(obj):
    '''Safe len().
    '''
    try:
        return len(obj)
    except TypeError:  # no len()
        return 0

def _len_array(obj):
    '''Array length in bytes.
    '''
    return len(obj) * obj.itemsize

def _len_bytearray(obj):
    '''Bytearray size.
    '''
    return obj.__alloc__()

def _len_code(obj):  # see .../Lib/test/test_sys.py
    '''Length of code object (stack and variables only).
    '''
    return obj.co_stacksize +      obj.co_nlocals  \
                            + _len(obj.co_freevars) \
                            + _len(obj.co_cellvars) - 1

def _len_dict(obj):
    '''Dict length in items (estimate).
    '''
    n = len(obj)  # active items
    if n < 6:  # ma_smalltable ...
       n = 0  # ... in basicsize
    else:  # at least one unused
       n = _power2(n + 1)
    return n

def _len_frame(obj):
    '''Length of a frame object.
    '''
    c = getattr(obj, 'f_code', None)
    if c:
       n = _len_code(c)
    else:
       n = 0
    return n

_digit2p2 =  1 << (sizes._sizeof_Cdigit << 3)
_digitmax = _digit2p2 - 1  # == (2 * PyLong_MASK + 1)
_digitlog =  1.0 / log(_digit2p2)

def _len_int(obj):
    '''Length of multi-precision int (aka long) in digits.
    '''
    if obj:
        n, i = 1, abs(obj)
        if i > _digitmax:
             # no log(x[, base]) in Python 2.2
            n += int(log(i) * _digitlog)
    else:  # zero
        n = 0
    return n

def _len_iter(obj):
    '''Length (hint) of an iterator.
    '''
    n = getattr(obj, '__length_hint__', None)
    if n:
       n = n()
    else:  # try len()
       n = _len(obj)
    return n

def _len_list(obj):
    '''Length of list (estimate).
    '''
    n = len(obj)
     # estimate over-allocation
    if n > 8:
       n += 6 + (n >> 3)
    elif n:
       n += 4
    return n

def _len_module(obj):
    '''Module length.
    '''
    return _len(obj.__dict__)  # _len(dir(obj))

def _len_set(obj):
    '''Length of frozen/set (estimate).
    '''
    n = len(obj)
    if n > 8:  # assume half filled
       n = _power2(n + n - 2)
    elif n:  # at least 8
       n = 8
    return n

def _len_slice(obj):
    '''Slice length.
    '''
    try:
        return ((obj.stop - obj.start + 1) // obj.step)
    except (AttributeError, TypeError):
        return 0

def _len_slots(obj):
    '''Slots length.
    '''
    return len(obj) - 1

def _len_struct(obj):
    '''Struct length in bytes.
    '''
    try:
        return obj.size
    except AttributeError:
        return 0

def _len_unicode(obj):
    '''Unicode size.
    '''
    return len(obj) + 1

_all_lengs = (None, _len,        _len_array,  _len_bytearray,
                    _len_code,   _len_dict,   _len_frame,
                    _len_int,    _len_iter,   _len_list,
                    _len_module, _len_set,    _len_slice,
                    _len_slots,  _len_struct, _len_unicode)
