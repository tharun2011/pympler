 # type-specific referent functions

from inspect    import isbuiltin, isclass, iscode, isframe, \
                       isfunction, ismethod, ismodule, stack
from math       import log
import types    as     Types
import weakref  as     Weakref

import common
import compat
import sizes
import type_common
import type_repo

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
    return type_common._refs(obj, named, '__class__', '__dict__',  '__doc__', '__mro__',
                             '__name__',  '__slots__', '__weakref__')

def _co_refs(obj, named):
    '''Return specific referents of a code object.
    '''
    return type_common._refs(obj, named, pref='co_')

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
    return type_common._refs(obj, named, '__doc__')

def _exc_refs(obj, named):
    '''Return specific referents of an Exception object.
    '''
     # .message raises DeprecationWarning in Python 2.6
    return type_common._refs(obj, named, 'args', 'filename', 'lineno', 'msg', 'text')  # , 'message', 'mixed'

def _file_refs(obj, named):
    '''Return specific referents of a file object.
    '''
    return type_common._refs(obj, named, 'mode', 'name')

def _frame_refs(obj, named):
    '''Return specific referents of a frame object.
    '''
    return type_common._refs(obj, named, pref='f_')

def _func_refs(obj, named):
    '''Return specific referents of a function or lambda object.
    '''
    return type_common._refs(obj, named, '__doc__', '__name__', '__code__',
                             pref='func_', excl=('func_globals',))

def _gen_refs(obj, named):
    '''Return the referent(s) of a generator object.
    '''
     # only some gi_frame attrs
    f = getattr(obj, 'gi_frame', None)
    return type_common._refs(f, named, 'f_locals', 'f_code')

def _im_refs(obj, named):
    '''Return specific referents of a method object.
    '''
    return type_common._refs(obj, named, '__doc__', '__name__', '__code__', pref='im_')

def _inst_refs(obj, named):
    '''Return specific referents of a class instance.
    '''
    return type_common._refs(obj, named, '__dict__', '__class__', slots='__slots__')

def _iter_refs(obj, named):
    '''Return the referent(s) of an iterator object.
    '''
    r = compat._getreferents(obj)  # special case
    return type_common._refs(r, named, itor=common._nameof(obj) or 'iteref')

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
    return type_common._refs(obj, named, '__doc__', pref='f')

def _seq_refs(obj, unused):  # named unused for PyChecker
    '''Return specific referents of a frozen/set, list, tuple and xrange object.
    '''
    return obj  # XXX for r in obj: yield r

def _stat_refs(obj, named):
    '''Return referents of a os.stat object.
    '''
    return type_common._refs(obj, named, pref='st_')

def _statvfs_refs(obj, named):
    '''Return referents of a os.statvfs object.
    '''
    return type_common._refs(obj, named, pref='f_')

def _tb_refs(obj, named):
    '''Return specific referents of a traceback object.
    '''
    return type_common._refs(obj, named, pref='tb_')

def _weak_refs(obj, unused):  # named unused for PyChecker
    '''Return weakly referent object.
    '''
    try:  # ignore 'key' of KeyedRef
        return (obj(),)
    except:  # XXX ReferenceError
        return ()  #PYCHOK OK

type_repo._all_refs = (None, _class_refs,   _co_refs,   _dict_refs,  _enum_refs,
                       _exc_refs,     _file_refs, _frame_refs, _func_refs,
                       _gen_refs,     _im_refs,   _inst_refs,  _iter_refs,
                       _module_refs,  _prop_refs, _seq_refs,   _stat_refs,
                       _statvfs_refs, _tb_refs,   type_common._type_refs,  _weak_refs)


 # type-specific length functions

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
                            + type_common._len(obj.co_freevars) \
                            + type_common._len(obj.co_cellvars) - 1

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
       n = type_common._len(obj)
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
    return type_common._len(obj.__dict__)  # type_common._len(dir(obj))

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

type_repo._all_lengs = (None, type_common._len,        _len_array,  _len_bytearray,
                        _len_code,   _len_dict,   _len_frame,
                        _len_int,    _len_iter,   _len_list,
                        _len_module, _len_set,    _len_slice,
                        _len_slots,  _len_struct, _len_unicode)



def _typedef(obj, derive=False, infer=False):
    '''Create a new typedef for an object.
    '''
    t =  type(obj)
    v = type_repo._Typedef(base=common._basicsize(t, obj=obj),
                 kind=type_repo._kind_dynamic, type=t)
  ##_printf('new %r %r/%r %s', t, common._basicsize(t), common._itemsize(t), common._repr(dir(obj)))
    if ismodule(obj):  # handle module like dict
        v.dup(item=type_repo._dict_typedef.item + sizes._sizeof_CPyModuleObject,
              leng=_len_module,
              refs=_module_refs)
    elif isframe(obj):
        v.set(base=common._basicsize(t, base=sizes._sizeof_CPyFrameObject, obj=obj),
              item=common._itemsize(t),
              leng=_len_frame,
              refs=_frame_refs)
    elif iscode(obj):
        v.set(base=common._basicsize(t, base=sizes._sizeof_CPyCodeObject, obj=obj),
              item=sizes._sizeof_Cvoidp,
              leng=_len_code,
              refs=_co_refs,
              both=False)  # code only
    elif compat._callable(obj):
        if isclass(obj):  # class or type
            v.set(refs=_class_refs,
                  both=False)  # code only
            if obj.__module__ in common._builtin_modules:
                v.set(kind=type_repo._kind_ignored)
        elif isbuiltin(obj):  # function or method
            v.set(both=False,  # code only
                  kind=type_repo._kind_ignored)
        elif isfunction(obj):
            v.set(refs=_func_refs,
                  both=False)  # code only
        elif ismethod(obj):
            v.set(refs=_im_refs,
                  both=False)  # code only
        elif isclass(t):  # callable instance, e.g. SCons,
             # handle like any other instance further below
            v.set(item=common._itemsize(t), safe_len=True,
                  refs=_inst_refs)  # not code only!
        else:
            v.set(both=False)  # code only
    elif _issubclass(t, dict):
        v.dup(kind=type_repo._kind_derived)
    elif _isdictclass(obj) or (infer and _infer_dict(obj)):
        v.dup(kind=type_repo._kind_inferred)
    elif getattr(obj, '__module__', None) in common._builtin_modules:
        v.set(kind=type_repo._kind_ignored)
    else:  # assume an instance of some class
        if derive:
            p = _derive_typedef(t)
            if p:  # duplicate parent
                v.dup(other=p, kind=type_repo._kind_derived)
                return v
        if _issubclass(t, Exception):
            v.set(item=common._itemsize(t), safe_len=True,
                  refs=_exc_refs,
                  kind=type_repo._kind_derived)
        elif isinstance(obj, Exception):
            v.set(item=common._itemsize(t), safe_len=True,
                  refs=_exc_refs)
        else:
            v.set(item=common._itemsize(t), safe_len=True,
                  refs=_inst_refs)
    return v

def _typedefof(obj, save=False, **opts):
    '''Get the typedef for an object.
    '''
    k = type_common._objkey(obj)
    v = type_repo._typedefs.get(k, None)
    if not v:  # new typedef
        v = _typedef(obj, **opts)
        if save:
            _typedefs[k] = v
    return v

def _derive_typedef(typ):
    '''Return single, existing super type typedef or None.
    '''
    v = [v for v in compat._values(type_repo._typedefs) if _issubclass(typ, v.type)]
    if len(v) == 1:
        return v[0]
    return None

def _isdictclass(obj):
    '''Return True for known dict objects.
    '''
    c = getattr(obj, '__class__', None)
    return c and c.__name__ in type_repo._dict_classes.get(c.__module__, ())

def _issubclass(sub, sup):
    '''Safe issubclass().
    '''
    if sup is not object:
        try:
            return issubclass(sub, sup)
        except TypeError:
            pass
    return False

def _infer_dict(obj):
    '''Return True for likely dict object.
    '''
    for ats in (('__len__', 'get', 'has_key',     'items',     'keys',     'values'),
                ('__len__', 'get', 'has_key', 'iteritems', 'iterkeys', 'itervalues')):
        for a in ats:  # no all(<generator_expression>) in Python 2.2
            if not compat._callable(getattr(obj, a, None)):
                break
        else:  # all True
            return True
    return False


 # static typedefs for data and code types
type_repo._typedef_both(complex)
type_repo._typedef_both(float)
type_repo._typedef_both(list,     refs=_seq_refs, leng=_len_list, item=sizes._sizeof_Cvoidp)  # sizeof(PyObject*)
type_repo._typedef_both(tuple,    refs=_seq_refs, leng=type_common._len,      item=sizes._sizeof_Cvoidp)  # sizeof(PyObject*)
type_repo._typedef_both(property, refs=_prop_refs)
type_repo._typedef_both(type(Ellipsis))
type_repo._typedef_both(type(None))

 # _Slots is a special tuple, see _Slots.__doc__
type_repo._typedef_both(common._Slots, item=sizes._sizeof_Cvoidp,
                      leng=_len_slots,  # length less one
                      refs=None,  # but no referents
                      heap=True)  # plus head

 # dict, dictproxy, dict_proxy and other dict-like types
type_repo._dict_typedef = type_repo._typedef_both(dict,        item=sizes._sizeof_CPyDictEntry, leng=_len_dict, refs=_dict_refs)
try:  # <type dictproxy> only in Python 2.x
    type_repo._typedef_both(Types.DictProxyType,     item=sizes._sizeof_CPyDictEntry, leng=_len_dict, refs=_dict_refs)
except AttributeError:  # XXX any class __dict__ is <type dict_proxy> in Python 3.0?
    type_repo._typedef_both(type(type_repo._Typedef.__dict__), item=sizes._sizeof_CPyDictEntry, leng=_len_dict, refs=_dict_refs)
 # other dict-like classes and types may be derived or inferred,
 # provided the module and class name is listed here (see functions
 # adict, _isdictclass and _infer_dict for further details)
type_repo._dict_classes = {'UserDict': ('IterableUserDict',  'UserDict'),
                 'weakref' : ('WeakKeyDictionary', 'WeakValueDictionary')}
try:  # <type module> is essentially a dict
    type_repo._typedef_both(Types.ModuleType, base=type_repo._dict_typedef.base,
                                    item=type_repo._dict_typedef.item + sizes._sizeof_CPyModuleObject,
                                    leng=_len_module, refs=_module_refs)
except AttributeError:  # missing
    pass

 # newer or obsolete types
try:
    from array import array  # array type
    type_repo._typedef_both(array, leng=_len_array, item=sizes._sizeof_Cbyte)
except ImportError:  # missing
    pass

try:  # bool has non-zero __itemsize__ in 3.0
    type_repo._typedef_both(bool)
except NameError:  # missing
    pass

try:  # ignore basestring
    type_repo._typedef_both(basestring, leng=None)
except NameError:  # missing
    pass

try:
    if isbuiltin(buffer):  # Python 2.2
        type_repo._typedef_both(type(buffer('')), item=sizes._sizeof_Cbyte, leng=type_common._len)  # XXX len in bytes?
    else:
        type_repo._typedef_both(buffer,           item=sizes._sizeof_Cbyte, leng=type_common._len)  # XXX len in bytes?
except NameError:  # missing
    pass

try:
    type_repo._typedef_both(bytearray, item=sizes._sizeof_Cbyte, leng=_len_bytearray)  #PYCHOK bytearray new in 2.6, 3.0
except NameError:  # missing
    pass
try:
    if type(bytes) is not type(str):  # bytes is str in 2.6 #PYCHOK bytes new in 2.6, 3.0
      type_repo._typedef_both(bytes, item=sizes._sizeof_Cbyte, leng=type_common._len)  #PYCHOK bytes new in 2.6, 3.0
except NameError:  # missing
    pass
try:  # XXX like bytes
    type_repo._typedef_both(str8, item=sizes._sizeof_Cbyte, leng=type_common._len)  #PYCHOK str8 new in 2.6, 3.0
except NameError:  # missing
    pass

try:
    type_repo._typedef_both(enumerate, refs=_enum_refs)
except NameError:  # missing
    pass

try:  # Exception is type in Python 3.0
    type_repo._typedef_both(Exception, refs=_exc_refs)
except:  # missing
    pass  #PYCHOK OK

try:
    type_repo._typedef_both(file, refs=_file_refs)
except NameError:  # missing
    pass

try:
    type_repo._typedef_both(frozenset, item=sizes._sizeof_Csetentry, leng=_len_set, refs=_seq_refs)
except NameError:  # missing
    pass
try:
    type_repo._typedef_both(set,       item=sizes._sizeof_Csetentry, leng=_len_set, refs=_seq_refs)
except NameError:  # missing
    pass

try:  # not callable()
    type_repo._typedef_both(Types.GetSetDescriptorType)
except AttributeError:  # missing
    pass

try:  # if long exists, it is multi-precision ...
    type_repo._typedef_both(long, item=sizes._sizeof_Cdigit, leng=_len_int)
    type_repo._typedef_both(int)  # ... and int is fixed size
except NameError:  # no long, only multi-precision int in Python 3.0
    type_repo._typedef_both(int,  item=sizes._sizeof_Cdigit, leng=_len_int)

try:  # not callable()
    type_repo._typedef_both(Types.MemberDescriptorType)
except AttributeError:  # missing
    pass

try:
    type_repo._typedef_both(type(NotImplemented))  # == Types.NotImplementedType
except NameError:  # missing
    pass

try:
    type_repo._typedef_both(range)
except NameError:  # missing
    pass
try:
    type_repo._typedef_both(xrange)
except NameError:  # missing
    pass

try:
    type_repo._typedef_both(reversed, refs=_enum_refs)
except NameError:  # missing
    pass

try:
    type_repo._typedef_both(slice, item=sizes._sizeof_Cvoidp, leng=_len_slice)  # XXX worst-case itemsize?
except NameError:  # missing
    pass

try:
    from os import curdir, stat, statvfs
    type_repo._typedef_both(type(stat(   curdir)), refs=_stat_refs)     # stat_result
    type_repo._typedef_both(type(statvfs(curdir)), refs=_statvfs_refs,  # statvfs_result
                                         item=sizes._sizeof_Cvoidp, leng=type_common._len)
except ImportError:  # missing
    pass

try:
    from struct import Struct  # only in Python 2.5 and 3.0
    type_repo._typedef_both(Struct, item=sizes._sizeof_Cbyte, leng=_len_struct)  # len in bytes
except ImportError:  # missing
    pass

try:
    type_repo._typedef_both(Types.TracebackType, refs=_tb_refs)
except AttributeError:  # missing
    pass

try:
    type_repo._typedef_both(unicode, leng=_len_unicode, item=sizes._sizeof_Cunicode)
    type_repo._typedef_both(str,     leng=type_common._len,         item=sizes._sizeof_Cbyte)  # 1-byte char
except NameError:  # str is unicode
    type_repo._typedef_both(str,     leng=_len_unicode, item=sizes._sizeof_Cunicode)

try:  # <type 'KeyedRef'>
    type_repo._typedef_both(Weakref.KeyedRef, refs=_weak_refs, heap=True)  # plus head
except AttributeError:  # missing
    pass

try:  # <type 'weakproxy'>
    type_repo._typedef_both(Weakref.ProxyType)
except AttributeError:  # missing
    pass

try:  # <type 'weakref'>
    type_repo._typedef_both(Weakref.ReferenceType, refs=_weak_refs)
except AttributeError:  # missing
    pass

 # some other, callable types
type_repo._typedef_code(object,     kind=type_repo._kind_ignored)
type_repo._typedef_code(super,      kind=type_repo._kind_ignored)
type_repo._typedef_code(common._Type_type, kind=type_repo._kind_ignored)

try:
    type_repo._typedef_code(classmethod, refs=_im_refs)
except NameError:
    pass
try:
    type_repo._typedef_code(staticmethod, refs=_im_refs)
except NameError:
    pass
try:
    type_repo._typedef_code(Types.MethodType, refs=_im_refs)
except NameError:
    pass

try:  # generator, code only, no len(), not callable()
    type_repo._typedef_code(Types.GeneratorType, refs=_gen_refs)
except AttributeError:  # missing
    pass

try:  # <type 'weakcallableproxy'>
    type_repo._typedef_code(Weakref.CallableProxyType, refs=_weak_refs)
except AttributeError:  # missing
    pass

 # any type-specific iterators
s = [compat._items({}), compat._keys({}), compat._values({})]
try:  # reversed list and tuples iterators
    s.extend([reversed([]), reversed(())])
except NameError:  # missing
    pass
try:  # range iterator
    s.append(xrange(1))
except NameError:  # missing
    pass
try:  # callable-iterator
    from re import finditer
    s.append(finditer('', ''))
except ImportError:  # missing
    pass
for t in compat._values(type_repo._typedefs):
    if t.type and t.leng:
        try:  # create an (empty) instance
            s.append(t.type())
        except TypeError:
            pass
for t in s:
    try:
        i = iter(t)
        type_repo._typedef_both(type(i), leng=_len_iter, refs=_iter_refs, item=0)  # no itemsize!
    except (KeyError, TypeError):  # ignore non-iterables, duplicates, etc.
        pass
del i, s, t
