import types    as     Types

import common
import compat

def _len(obj):
    '''Safe len().
    '''
    try:
        return len(obj)
    except TypeError:  # no len()
        return 0

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


def _type_refs(obj, named):
    '''Return specific referents of a type object.
    '''
    return _refs(obj, named, '__dict__', '__doc__', '__mro__',
                             '__name__', '__slots__', '__weakref__')



# more private functions and classes

_old_style = '*'  # marker
_new_style = ''   # no marker

class _Claskey(object):
    '''Wrapper for class objects.
    '''
    __slots__ = ('_obj', '_sty')

    def __init__(self, obj, style):
        self._obj = obj  # XXX Weakref.ref(obj)
        self._sty = style

    def __str__(self):
        r = str(self._obj)
        if r.endswith('>'):
            r = '%s%s def>' % (r[:-1], self._sty)
        elif self._sty is _old_style and not r.startswith('class '):
            r = 'class %s%s def' % (r, self._sty)
        else:
            r = '%s%s def' % (r, self._sty)
        return r
    __repr__ = __str__

 # For most objects, the object type is used as the key in the
 # _typedefs dict further below, except class and type objects
 # and old-style instances.  Those are wrapped with separate
 # _Claskey or _Instkey instances to be able (1) to distinguish
 # instances of different old-style classes by class, (2) to
 # distinguish class (and type) instances from class (and type)
 # definitions for new-style classes and (3) provide similar
 # results for repr() and str() of new- and old-style classes
 # and instances.

_claskeys = {}  # [id(obj)] = _Claskey()

def _claskey(obj, style):
    '''Wrap an old- or new-style class object.
    '''
    i =  id(obj)
    k = _claskeys.get(i, None)
    if not k:
        _claskeys[i] = k = _Claskey(obj, style)
    return k

try:  # no Class- and InstanceType in Python 3.0
    _Types_ClassType    = Types.ClassType
    _Types_InstanceType = Types.InstanceType

    class _Instkey(object):
        '''Wrapper for old-style class (instances).
        '''
        __slots__ = ('_obj',)

        def __init__(self, obj):
            self._obj = obj  # XXX Weakref.ref(obj)

        def __str__(self):
            return '<class %s.%s%s>' % (self._obj.__module__, self._obj.__name__, _old_style)
        __repr__ = __str__

    _instkeys = {}  # [id(obj)] = _Instkey()

    def _instkey(obj):
        '''Wrap an old-style class (instance).
        '''
        i =  id(obj)
        k = _instkeys.get(i, None)
        if not k:
            _instkeys[i] = k = _Instkey(obj)
        return k

    def _keytuple(obj):
        '''Return class and instance keys for a class.
        '''
        t = type(obj)
        if t is _Types_InstanceType:
            t = obj.__class__
            return _claskey(t,   _old_style), _instkey(t)
        elif t is _Types_ClassType:
            return _claskey(obj, _old_style), _instkey(obj)
        elif t is common._Type_type:
            return _claskey(obj, _new_style), obj
        return None, None  # not a class

    def _objkey(obj):
        '''Return the key for any object.
        '''
        k = type(obj)
        if k is _Types_InstanceType:
            k = _instkey(obj.__class__)
        elif k is _Types_ClassType:
            k = _claskey(obj, _old_style)
        elif k is common._Type_type:
            k = _claskey(obj, _new_style)
        return k

except AttributeError:  # Python 3.0

    def _keytuple(obj):  #PYCHOK expected
        '''Return class and instance keys for a class.
        '''
        if type(obj) is common._Type_type:  # isclass(obj):
            return _claskey(obj, _new_style), obj
        return None, None  # not a class

    def _objkey(obj):  #PYCHOK expected
        '''Return the key for any object.
        '''
        k = type(obj)
        if k is common._Type_type:  # isclass(obj):
            k = _claskey(obj, _new_style)
        return k
