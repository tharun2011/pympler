#!/usr/bin/env python

# Copyright, license and disclaimer are at the end of this file.

# This is the latest, enhanced version of the asizeof.py recipes at
# <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/546530>
# <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/544288>

'''
This module exposes 9 functions and 2 classes to obtain lengths and
sizes of Python objects (for Python 2.2 or later [#test]_).

**Public Functions** [#unsafe]_

   Function **asizeof** calculates the combined (approximate) size
   of one or several Python objects in bytes.  Function **asizesof**
   returns a tuple containing the (approximate) size in bytes for
   each given Python object separately.  Function **asized** returns
   for each object an instance of class **Asized** containing all the
   size information of the object and a tuple with the referents.

   Functions **basicsize** and **itemsize** return the basic resp. item
   size of the given object.

   Function **flatsize** returns the flat size of a Python object in
   bytes defined as the basic size plus the item size times the
   length of the given object.

   Function **leng** returns the length of an object, like standard
   ``len`` but extended for several types, e.g. the **leng** of a
   multi-precision int (or long) is the number of ``digits`` [#digit]_.
   The length of most mutable sequence objects includes an estimate of
   the over-allocation and therefore, the **leng** value may differ
   from the standard ``len`` result.

   Function **refs** returns (a generator for) the referents of the
   given object, i.e. the objects referenced by the given object.

   Certain classes are known to be sub-classes of or to behave as
   dict objects.  Function **adict** can be used to install other
   class objects to be treated like dict.

**Public Classes** [#unsafe]_

   An instance of class **Asized** is returned for each object sized
   with the **asized** function or method.

   Class **Asizer** may be used to accumulate the results of several
   **asizeof** or **asizesof** calls.  After creating an **Asizer** instance,
   use methods **asizeof** and **asizesof** as needed to size any
   number of additional objects.

   Call methods **exclude_refs** and/or **exclude_types** to exclude
   references to resp. instances or types of certain objects.
   Use one of the **print\_... methods** to report the statistics.

**Duplicate Objects**

   Any duplicate, given objects are sized only once and the size
   is included in the combined total only once.  But functions
   **asizesof** and **asized** do return a size value resp. an
   **Asized** instance for each given object, including duplicates.

**Definitions** [#arb]_

   The size of an object is defined as the sum of the flat size
   of the object plus the sizes of any referents.  Referents are
   visited recursively up to a given limit.  However, the size
   of objects referenced multiple times is included only once.

   The flat size of an object is defined as the basic size of the
   object plus the item size times the number of allocated items.
   The flat size does include the size for the items (references
   to the referents), but not the referents themselves.

   The flat size returned by function **flatsize** equals the result
   of the **asizeof** function with options *code=True*, *ignored=False*,
   *limit=0* and option *align* set to the same value.

   The accurate flat size for an object is obtained from function
   ``sys.getsizeof()`` where available.  Otherwise, the length and
   size of sequence objects as dicts, lists, sets, etc. is based
   on an estimate for the number of allocated items.  As a result,
   the reported length and size may substantially differ from the
   actual length and size.

   The basic and item sizes are obtained from the ``__basicsize__``
   resp. ``__itemsize__`` attributes of the (type of the) object.
   Where necessary (e.g. sequence objects), a zero ``__itemsize__``
   is replaced by the size of a corresponding C type.  The basic
   size (of GC managed objects) objects includes the overhead for
   Python's garbage collector (GC) as well as the space needed for
   ``refcounts`` (used only in certain Python builds).

   Optionally, size values can be aligned to any power of 2 multiple.

**Size of (byte)code**

   The (byte)code size of objects like classes, functions, methods,
   modules, etc. can be included by setting option *code=True*.

   Iterators are handled similar to sequences: iterated object(s)
   are sized like referents, only if the recursion *limit* permits.
   Also, function ``gc.get_referents()`` must return the referent
   object of iterators.

   Generators are sized as (byte)code only, but the generated
   objects are never sized.

**Old- and New-style Classes**

   All old- and new-style class, instance and type objects, are
   handled uniformly such that (a) instance objects are distinguished
   from class objects and (b) instances of different old-style classes
   can be dealt with separately.

   Class and type objects are represented as <class ....* def>
   resp. <type ... def> where an '*' indicates an old-style class
   and the  def suffix marks the definition object.  Instances of
   old-style classes are shown as new-style ones but with an '*'
   at the end of the name, like <class module.name*>.

**Ignored Objects**

   To avoid excessive sizes, several object types are ignored [#arb]_ by
   default, e.g. built-in functions, built-in types and classes [#bi]_,
   function globals and module referents.  However, any instances
   thereof are sized and module objects will be sized when passed
   as given objects.  Ignored object types are included if option
   *ignored* is set accordingly.

   In addition, many ``__...__`` attributes of callable objects are
   ignored [#arb]_, except crucial ones, e.g. class attributes ``__dict__``,
   ``__doc__``, ``__name__`` and ``__slots__``.  For more details, see the
   type-specific ``type_spec._..._refs()`` and ``type_spec._len_...()`` functions below.

.. rubric:: Footnotes
.. [#unsafe] The functions and classes in this module are not thread-safe.

.. [#digit] See Python source file ``.../Include/longinterp.h`` for the
     C ``typedef`` of ``digit`` used in multi-precision int (or
     long) objects.  The C ``sizeof(digit)`` in bytes can be obtained
     in Python from the int (or long) ``__itemsize__`` attribute.
     Function **leng** determines the number of ``digits`` of an
     int (or long) value.

.. [#arb] These definitions and other assumptions are rather arbitrary
     and may need corrections or adjustments.

.. [#bi] Types and classes are considered built-in if the ``__module__``
     of the type or class is listed in ``_builtin_modules`` below.

.. [#test] Tested with Python 2.2.3, 2.3.7, 2.4.5, 2.5.1, 2.5.2, 2.6 or
     3.0 on CentOS 4.6, SuSE 9.3, MacOS X 10.4.11 Tiger (Intel) and
     Panther 10.3.9 (PPC), Solaris 10 and Windows XP all 32-bit Python
     and on RHEL 3u7 and Solaris 10 both 64-bit Python.


'''  #PYCHOK expected

from __future__ import generators  #PYCHOK for yield in Python 2.2

from inspect    import isbuiltin, isclass, iscode, isframe, \
                       isfunction, ismethod, ismodule, stack
from os         import linesep
import sys
import types    as     Types
import weakref  as     Weakref

import common
import compat
import demos
import sizes
import type_common
import type_repo
import type_spec

__version__ = '5.10 (Dec 04, 2008)'
__all__     = ['adict', 'asized', 'asizeof', 'asizesof',
               'Asized', 'Asizer',  # classes
               'basicsize', 'flatsize', 'itemsize', 'leng', 'refs']



 # private functions

def _kwdstr(**kwds):
    '''Keyword arguments as a string.
    '''
    return ', '.join(compat._sorted(['%s=%r' % kv for kv in compat._items(kwds)]))  # [] for Python 2.2

def _lengstr(obj):
    '''Object length as a string.
    '''
    n = leng(obj)
    if n is None:  # no len
       r = ''
    elif n > type_common._len(obj):  # extended
       r = ' leng %d!' % n
    else:
       r = ' leng %d' % n
    return r

def _objs_opts(objs, all=None, **opts):
    '''Return given or 'all' objects
       and the remaining options.
    '''
    if objs:  # given objects
        t = objs
    elif all in (False, None):
        t = ()
    elif all is True:  # 'all' objects ...
         # ... modules first, globals and stack
         # (may contain duplicate objects)
        t = tuple(compat._values(sys.modules)) + (
            globals(), stack(sys.getrecursionlimit()))
    else:
        raise ValueError('invalid option: %s=%r' % ('all', all))
    return t, opts  #PYCHOK OK

def _p100(part, total, prec=1):
    '''Return percentage as string.
    '''
    r = float(total)
    if r:
        r = part * 100.0 / r
        return '%.*f%%' % (prec, r)
    return 'n/a'

def _plural(num):
    '''Return 's' if plural.
    '''
    if num == 1:
        s = ''
    else:
        s = 's'
    return s

def _prepr(obj, clip=0):
    '''Prettify and clip long repr() string.
    '''
    return common._repr(obj, clip=clip).strip('<>').replace("'", '')  # remove <''>

def _SI(size, K=1024, i='i'):
    '''Return size as SI string.
    '''
    if 1 < K < size:
        f = float(size)
        for si in iter('KMGPTE'):
            f /= K
            if f < K:
                return ' or %.1f %s%sB' % (f, si, i)
    return ''

def _SI2(size, **kwds):
    '''Return size as regular plus SI string.
    '''
    return str(size) + _SI(size, **kwds)



class _Prof(object):
    '''Internal type profile class.
    '''
    total  = 0     # total size
    high   = 0     # largest size
    number = 0     # number of (unique) objects
    objref = None  # largest object (weakref)
    weak   = False # objref is weakref(object)

    def __cmp__(self, other):
        if self.total < other.total:
            return -1
        if self.total > other.total:
            return +1
        if self.number < other.number:
            return -1
        if self.number > other.number:
            return +1
        return 0

    def __lt__(self, other):  # for Python 3.0
        return self.__cmp__(other) < 0

    def format(self, clip=0, grand=None):
        '''Return format dict.
        '''
        if self.number > 1:  # avg., plural
            a, p = int(self.total / self.number), 's'
        else:
            a, p = self.total, ''
        o = self.objref
        if self.weak:  # weakref'd
            o = o()
        t = _SI2(self.total)
        if grand:
            t += ' (%s)' % _p100(self.total, grand, prec=0)
        return compat._kwds(avg=_SI2(a),         high=_SI2(self.high),
                     lengstr=_lengstr(o), obj=common._repr(o, clip=clip),
                     plural=p,            total=t)

    def update(self, obj, size):
        '''Update this profile.
        '''
        self.number += 1
        self.total  += size
        if self.high < size:  # largest
           self.high = size
           try:  # prefer using weak ref
               self.objref, self.weak = Weakref.ref(obj), True
           except TypeError:
               self.objref, self.weak = obj, False


 # public classes

class Asized(object):
    '''Store the results of an **asized** object
       in these 4 attributes:

         *size*  -- total size of the object

         *flat*  -- flat size of the object

         *name*  -- name or ``repr`` of the object

         *refs*  -- tuple containing an **Asized** instance for each referent
    '''
    def __init__(self, size, flat, refs=(), name=None):
        self.size = size  # total size
        self.flat = flat  # flat size
        self.name = name  # name, repr or None
        self.refs = tuple(refs)

    def __str__(self):
        return 'size %r, flat %r, refs[%d], name %r' % (
                self.size, self.flat, len(self.refs), self.name)

class Asizer(object):
    '''Sizer state and options.
    '''
    _align_    = 8
    _clip_     = 80
    _code_     = False
    _derive_   = False
    _detail_   = 0  # for Asized only
    _infer_    = False
    _limit_    = 100
    _stats_    = 0

    _cutoff    = 0  # in percent
    _depth     = 0  # recursion depth
    _duplicate = 0
    _excl_d    = None  # {}
    _ign_d     = type_repo._kind_ignored
    _incl      = ''  # or ' (incl. code)'
    _mask      = 7   # see _align_
    _missed    = 0   # due to errors
    _profile   = False
    _profs     = None  # {}
    _seen      = None  # {}
    _total     = 0   # total size

    def __init__(self, **opts):
        '''See method **reset** for the available options.
        '''
        self._excl_d = {}
        self.reset(**opts)

    def _clear(self):
        '''Clear state.
        '''
        self._depth     = 0   # recursion depth
        self._duplicate = 0
        self._incl      = ''  # or ' (incl. code)'
        self._missed    = 0   # due to errors
        self._profile   = False
        self._profs     = {}
        self._seen      = {}
        self._total     = 0   # total size
        for k in compat._keys(self._excl_d):
            self._excl_d[k] = 0

    def _nameof(self, obj):
        '''Return the object's name.
        '''
        return common._nameof(obj, '') or self._repr(obj)

    def _prepr(self, obj):
        '''Like **prepr()**.
        '''
        return _prepr(obj, clip=self._clip_)

    def _prof(self, key):
        '''Get _Prof object.
        '''
        p = self._profs.get(key, None)
        if not p:
            self._profs[key] = p = _Prof()
        return p

    def _repr(self, obj):
        '''Like ``repr()``.
        '''
        return common._repr(obj, clip=self._clip_)

    def _sizer(self, obj, deep, sized):
        '''Size an object, recursively.
        '''
        s, f, i = 0, 0, id(obj)
         # skip obj if seen before
         # or if ref of a given obj
        if i in self._seen:
            if deep:
                self._seen[i] += 1
                if sized:
                    s = sized(s, f, name=self._nameof(obj))
                return s
        else:
            self._seen[i] = 0
        try:
            k, rs = type_common._objkey(obj), []
            if k in self._excl_d:
                self._excl_d[k] += 1
            else:
                v = type_repo._typedefs.get(k, None)
                if not v:  # new typedef
                    type_repo._typedefs[k] = v = type_spec._typedef(obj, derive=self._derive_,
                                                     infer=self._infer_)
                if (v.both or self._code_) and v.kind is not self._ign_d:
                    s = f = v.flat(obj, self._mask)  # flat size
                    if self._profile:  # profile type
                        self._prof(k).update(obj, s)
                     # recurse, but not for nested modules
                    if v.refs and deep < self._limit_ and not (deep and ismodule(obj)):
                         # add sizes of referents
                        r, z, d = v.refs, self._sizer, deep + 1
                        if sized and deep < self._detail_:
                             # use named referents
                            for o in r(obj, True):
                                if isinstance(o, common._NamedRef):
                                    t = z(o.ref, d, sized)
                                    t.name = o.name
                                else:
                                    t = z(o, d, sized)
                                    t.name = self._nameof(o)
                                rs.append(t)
                                s += t.size
                        else:  # no sum(<generator_expression>) in Python 2.2
                            for o in r(obj, False):
                                s += z(o, d, None)
                         # recursion depth
                        if self._depth < d:
                           self._depth = d
            self._seen[i] += 1
        except RuntimeError:  # XXX RecursionLimitExceeded:
            self._missed += 1
        if sized:
            s = sized(s, f, name=self._nameof(obj), refs=rs)
        return s

    def _sizes(self, objs, sized=None):
        '''Return the size or an **Asized** instance for each
           given object and the total size.  The total
           includes the size of duplicates only once.
        '''
        self.exclude_refs(*objs)  # skip refs to objs
        s, t = {}, []
        for o in objs:
            i = id(o)
            if i in s:  # duplicate
                self._seen[i] += 1
                self._duplicate += 1
            else:
                s[i] = self._sizer(o, 0, sized)
            t.append(s[i])
        if sized:
            s = compat._sum([i.size for i in compat._values(s)])  # [] for Python 2.2
        else:
            s = compat._sum(compat._values(s))
        self._total += s  # accumulate
        return s, tuple(t)

    def asized(self, *objs, **opts):
        '''Size each object and return an **Asized** instance with
           size information and referents up to the given detail
           level (and with modified options, see method **set**).

           If only one object is given, the return value is the
           **Asized** instance for that object.
        '''
        if opts:
            self.set(**opts)
        _, t = self._sizes(objs, Asized)
        if len(t) == 1:
            t = t[0]
        return t

    def asizeof(self, *objs, **opts):
        '''Return the combined size of the given objects
           (with modified options, see method **set**).
        '''
        if opts:
            self.set(**opts)
        s, _ = self._sizes(objs, None)
        return s

    def asizesof(self, *objs, **opts):
        '''Return the individual sizes of the given objects
           (with modified options, see method  **set**).
        '''
        if opts:
            self.set(**opts)
        _, t = self._sizes(objs, None)
        return t

    def exclude_refs(self, *objs):
        '''Exclude any references to the specified objects from sizing.

           While any references to the given objects are excluded, the
           objects will be sized if specified as positional arguments
           in subsequent calls to methods **asizeof** and **asizesof**.
        '''
        for o in objs:
            self._seen.setdefault(id(o), 0)

    def exclude_types(self, *objs):
        '''Exclude the specified object instances and types from sizing.

           All instances and types of the given objects are excluded,
           even objects specified as positional arguments in subsequent
           calls to methods **asizeof** and **asizesof**.
        '''
        for o in objs:
            for t in type_common._keytuple(o):
                if t and t not in self._excl_d:
                    self._excl_d[t] = 0

    def print_profiles(self, w=0, cutoff=0, **print3opts):
        '''Print the profiles above *cutoff* percentage.

               *w=0*           -- indentation for each line

               *cutoff=0*      -- minimum percentage printed

               *print3options* -- print options, ala Python 3.0
        '''
         # get the profiles with non-zero size or count
        t = [(v, k) for k, v in compat._items(self._profs) if v.total > 0 or v.number > 1]
        if (len(self._profs) - len(t)) < 9:  # just show all
            t = [(v, k) for k, v in compat._items(self._profs)]
        if t:
            s = ''
            if self._total:
                s = ' (% of grand total)'
                c = max(cutoff, self._cutoff)
                c = int(c * 0.01 * self._total)
            else:
                c = 0
            common._printf('%s%*d profile%s:  total%s, average, and largest flat size%s:  largest object',
                     linesep, w, len(t), _plural(len(t)), s, self._incl, **print3opts)
            r = len(t)
            for v, k in compat._sorted(t, reverse=True):
                s = 'object%(plural)s:  %(total)s, %(avg)s, %(high)s:  %(obj)s%(lengstr)s' % v.format(self._clip_, self._total)
                common._printf('%*d %s %s', w, v.number, self._prepr(k), s, **print3opts)
                r -= 1
                if r > 1 and v.total < c:
                    c = max(cutoff, self._cutoff)
                    common._printf('%+*d profiles below cutoff (%.0f%%)', w, r, c)
                    break
            z = len(self._profs) - len(t)
            if z > 0:
                common._printf('%+*d %r object%s', w, z, 'zero', _plural(z), **print3opts)

    def print_stats(self, objs=(), opts={}, sized=(), sizes=(), stats=3.0, **print3opts):
        '''Print the statistics.

               *w=0*           -- indentation for each line

               *objs=()*       -- optional, list of objects

               *opts={}*       -- optional, dict of options used

               *sized=()*      -- optional, tuple of **Asized** instances returned

               *sizes=()*      -- optional, tuple of sizes returned

               *stats=0.0*     -- print stats, see function **asizeof**

               *print3options* -- print options, as in Python 3.0
        '''
        s = min(opts.get('stats', stats) or 0, self._stats_)
        if s > 0:  # print stats
            t = self._total + self._missed + compat._sum(compat._values(self._seen))
            w = len(str(t)) + 1
            t = c = ''
            o = _kwdstr(**opts)
            if o and objs:
                c = ', '
             # print header line(s)
            if sized and objs:
                n = len(objs)
                if n > 1:
                    common._printf('%sasized(...%s%s) ...', linesep, c, o, **print3opts)
                    for i in range(n):  # no enumerate in Python 2.2.3
                        common._printf('%*d: %s', w-1, i, sized[i], **print3opts)
                else:
                    common._printf('%sasized(%s): %s', linesep, o, sized, **print3opts)
            elif sizes and objs:
                common._printf('%sasizesof(...%s%s) ...', linesep, c, o, **print3opts)
                for z, o in zip(sizes, objs):
                    common._printf('%*d bytes%s%s:  %s', w, z, _SI(z), self._incl, self._repr(o), **print3opts)
            else:
                if objs:
                    t = self._repr(objs)
                common._printf('%sasizeof(%s%s%s) ...', linesep, t, c, o, **print3opts)
             # print summary
            self.print_summary(w=w, objs=objs, **print3opts)
            if s > 1:  # print profile
                c = int(s - int(s)) * 100
                self.print_profiles(w=w, cutoff=c, **print3opts)
                if s > 2:  # print typedefs
                    self.print_typedefs(w=w, **print3opts)

    def print_summary(self, w=0, objs=(), **print3opts):
        '''Print the summary statistics.

               *w=0*            -- indentation for each line

               *objs=()*        -- optional, list of objects

               *print3options*  -- print options, as in Python 3.0
        '''
        common._printf('%*d bytes%s%s', w, self._total, _SI(self._total), self._incl, **print3opts)
        if self._mask:
            common._printf('%*d byte aligned', w, self._mask + 1, **print3opts)
        common._printf('%*d byte sizeof(void*)', w, sizes._sizeof_Cvoidp, **print3opts)
        n = len(objs or ())
        if n > 0:
            d = self._duplicate or ''
            if d:
                d = ', %d duplicate' % self._duplicate
            common._printf('%*d object%s given%s', w, n, _plural(n), d, **print3opts)
        t = compat._sum([1 for t in compat._values(self._seen) if t != 0])  # [] for Python 2.2
        common._printf('%*d object%s sized', w, t, _plural(t), **print3opts)
        if self._excl_d:
            t = compat._sum(compat._values(self._excl_d))
            common._printf('%*d object%s excluded', w, t, _plural(t), **print3opts)
        t = compat._sum(compat._values(self._seen))
        common._printf('%*d object%s seen', w, t, _plural(t), **print3opts)
        if self._missed > 0:
            common._printf('%*d object%s missed', w, self._missed, _plural(self._missed), **print3opts)
        if self._depth > 0:
            common._printf('%*d recursion depth', w, self._depth, **print3opts)

    def print_typedefs(self, w=0, **print3opts):
        '''Print the types and dict tables.

               *w=0*            -- indentation for each line

               *print3options*  -- print options, as in Python 3.0
        '''
        for k in type_repo._all_kinds:
             # XXX Python 3.0 doesn't sort type objects
            t = [(self._prepr(a), v) for a, v in compat._items(type_repo._typedefs) if v.kind == k and (v.both or self._code_)]
            if t:
                common._printf('%s%*d %s type%s:  basicsize, itemsize, _len_(), _refs()',
                         linesep, w, len(t), k, _plural(len(t)), **print3opts)
                for a, v in compat._sorted(t):
                    common._printf('%*s %s:  %s', w, '', a, v, **print3opts)
         # dict and dict-like classes
        t = compat._sum([len(v) for v in compat._values(type_repo._dict_classes)])  # [] for Python 2.2
        if t:
            common._printf('%s%*d dict/-like classes:', linesep, w, t, **print3opts)
            for m, v in compat._items(type_repo._dict_classes):
                common._printf('%*s %s:  %s', w, '', m, self._prepr(v), **print3opts)

    def set(self, align=None, code=None, detail=None, limit=None, stats=None):
        '''Set some options.  See also **reset**.

               *align*   -- size alignment

               *code*    -- incl. (byte)code size

               *detail*  -- Asized refs level

               *limit*   -- recursion limit

               *stats*   -- print statistics, see function **asizeof**

        Any options not set remain unchanged from the previous setting.
        '''
         # adjust
        if align is not None:
            self._align_ = align
            if align > 1:
                self._mask = align - 1
                if (self._mask & align) != 0:
                    raise ValueError('invalid option: %s=%r' % ('align', align))
            else:
                self._mask = 0
        if code is not None:
            self._code_ = code
            if code:  # incl. (byte)code
                self._incl = ' (incl. code)'
        if detail is not None:
            self._detail_ = detail
        if limit is not None:
            self._limit_ = limit
        if stats is not None:
            self._stats_ = s = int(stats)
            self._cutoff = (stats - s) * 100
            if s > 1:  # profile types
                self._profile = True
            else:
                self._profile = False

    def _get_duplicate(self):
        '''Number of duplicate objects.
        '''
        return self._duplicate
    duplicate = property(_get_duplicate, doc=_get_duplicate.__doc__)

    def _get_missed(self):
        '''Number of objects missed due to errors.
        '''
        return self._missed
    missed = property(_get_missed, doc=_get_missed.__doc__)

    def _get_total(self):
        '''Total size accumulated so far.
        '''
        return self._total
    total = property(_get_total, doc=_get_total.__doc__)

    def reset(self, align=8,  clip=80,      code=False,  derive=False,
                    detail=0, ignored=True, infer=False, limit=100,  stats=0):
        '''Reset options, state, etc.

        The available options and default values are:

             *align=8*       -- size alignment

             *clip=80*       -- clip repr() strings

             *code=False*    -- incl. (byte)code size

             *derive=False*  -- derive from super type

             *detail=0*      -- Asized refs level

             *ignored=True*  -- ignore certain types

             *infer=False*   -- try to infer types

             *limit=100*     -- recursion limit

             *stats=0.0*     -- print statistics, see function **asizeof**

        See function **asizeof** for a description of the options.
        '''
         # options
        self._align_  = align
        self._clip_   = clip
        self._code_   = code
        self._derive_ = derive
        self._detail_ = detail  # for Asized only
        self._infer_  = infer
        self._limit_  = limit
        self._stats_  = stats
        if ignored:
            self._ign_d = type_repo._kind_ignored
        else:
            self._ign_d = None
         # clear state
        self._clear()
        self.set(align=align, code=code, stats=stats)


 # public functions

def adict(*classes):
    '''Install one or more classes to be handled as dict.
    '''
    a = True
    for c in classes:
         # if class is dict-like, add class
         # name to type_repo._dict_classes[module]
        if isclass(c) and _infer_dict(c):
            t = type_repo._dict_classes.get(c.__module__, ())
            if c.__name__ not in t:  # extend tuple
                type_repo._dict_classes[c.__module__] = t + (c.__name__,)
        else:  # not a dict-like class
            a = False
    return a  # all installed if True

_asizer = Asizer()

def asized(*objs, **opts):
    '''Return a tuple containing an **Asized** instance for each
       object passed as positional argment using the following
       options.

           *align=8*       -- size alignment

           *clip=80*       -- clip repr() strings

           *code=False*    -- incl. (byte)code size

           *derive=False*  -- derive from super type

           *detail=0*      -- Asized refs level

           *ignored=True*  -- ignore certain types

           *infer=False*   -- try to infer types

           *limit=100*     -- recursion limit

           *stats=0.0*     -- print statistics

       If only one object is given, the return value is the **Asized**
       instance for that object.  Otherwise, the length of the returned
       tuple matches the number of given objects.

       Set *detail* to the desired referents level (recursion depth).

       See function **asizeof** for descriptions of the other options.

    '''
    if 'all' in opts:
        raise KeyError('invalid option: %s=%r' % ('all', opts['all']))
    if objs:
        _asizer.reset(**opts)
        t = _asizer.asized(*objs)
        _asizer.print_stats(objs, opts=opts, sized=t)  # show opts as _kwdstr
        _asizer._clear()
    else:
        t = ()
    return t

def asizeof(*objs, **opts):
    '''Return the combined size in bytes of all objects passed as positional argments.

    The available options and defaults are the following.

         *align=8*       -- size alignment

         *all=False*     -- all current objects

         *clip=80*       -- clip ``repr()`` strings

         *code=False*    -- incl. (byte)code size

         *derive=False*  -- derive from super type

         *ignored=True*  -- ignore certain types

         *infer=False*   -- try to infer types

         *limit=100*     -- recursion limit

         *stats=0.0*     -- print statistics

    Set *align* to a power of 2 to align sizes.  Any value less
    than 2 avoids size alignment.

    All current module, global and stack objects are sized if
    *all* is True and if no positional arguments are supplied.

    A positive *clip* value truncates all repr() strings to at
    most *clip* characters.

    The (byte)code size of callable objects like functions,
    methods, classes, etc. is included only if *code* is True.

    If *derive* is True, new types are handled like an existing
    (super) type provided there is one and only of those.

    By default certain base types like object, super, etc. are
    ignored.  Set *ignored* to False to include those.

    If *infer* is True, new types are inferred from attributes
    (only implemented for dict types on callable attributes
    as get, has_key, items, keys and values).

    Set *limit* to a positive value to accumulate the sizes of
    the referents of each object, recursively up to the limit.
    Using *limit=0* returns the sum of the flat[4] sizes of
    the given objects.  High *limit* values may cause runtime
    errors and miss objects for sizing.

    A positive value for *stats* prints up to 8 statistics, (1)
    a summary of the number of objects sized and seen, (2) a
    simple profile of the sized objects by type and (3+) up to
    6 tables showing the static, dynamic, derived, ignored,
    inferred and dict types used, found resp. installed.  The
    fractional part of the *stats* value (x100) is the cutoff
    percentage for simple profiles.

    [4] See the documentation of this module for the definition of flat size.
    '''
    t, p = _objs_opts(objs, **opts)
    if t:
        _asizer.reset(**p)
        s = _asizer.asizeof(*t)
        _asizer.print_stats(objs=t, opts=opts)  # show opts as _kwdstr
        _asizer._clear()
    else:
        s = 0
    return s

def asizesof(*objs, **opts):
    '''Return a tuple containing the size in bytes of all objects
       passed as positional argments using the following options.

           *align=8*       -- size alignment

           *clip=80*       -- clip ``repr()`` strings

           *code=False*    -- incl. (byte)code size

           *derive=False*  -- derive from super type

           *ignored=True*  -- ignore certain types

           *infer=False*   -- try to infer types

           *limit=100*     -- recursion limit

           *stats=0.0*     -- print statistics

       See function **asizeof** for a description of the options.

       The length of the returned tuple equals the number of given
       objects.
    '''
    if 'all' in opts:
        raise KeyError('invalid option: %s=%r' % ('all', opts['all']))
    if objs:  # size given objects
        _asizer.reset(**opts)
        t = _asizer.asizesof(*objs)
        _asizer.print_stats(objs, opts=opts, sizes=t)  # show opts as _kwdstr
        _asizer._clear()
    else:
        t = ()
    return t

def basicsize(obj, **opts):
    '''Return the basic size of an object (in bytes).

       Valid options and defaults are

           *derive=False*  -- derive type from super type

           *infer=False*   -- try to infer types

           *save=False*    -- save typedef if new
    '''
    v = type_spec._typedefof(obj, **opts)
    if v:
        v = v.base
    return v

def flatsize(obj, align=0, **opts):
    '''Return the flat size of an object (in bytes),
       optionally aligned to a given power of 2.

       See function **basicsize** for a description of
       the other options.  See the documentation of
       this module for the definition of flat size.
    '''
    v = type_spec._typedefof(obj, **opts)
    if v:
        if align > 1:
            m = align - 1
            if (align & m) != 0:
                raise ValueError('invalid option: %s=%r' % ('align', align))
        else:
            m = 0
        v = v.flat(obj, m)
    return v

def itemsize(obj, **opts):
    '''Return the item size of an object (in bytes).

       See function **basicsize** for a description of
       the options.
    '''
    v = type_spec._typedefof(obj, **opts)
    if v:
        v = v.item
    return v

def leng(obj, **opts):
    '''Return the length of an object (in items).

       See function **basicsize** for a description of
       the options.
    '''
    v = type_spec._typedefof(obj, **opts)
    if v:
        v = v.leng
        if v and compat._callable(v):
            v = v(obj)
    return v

def refs(obj, **opts):
    '''Return (a generator for) specific referents of an
       object.

       See function **basicsize** for a description of
       the options.
    '''
    v = type_spec._typedefof(obj, **opts)
    if v:
        v = v.refs
        if v and compat._callable(v):
            v = v(obj, False)
    return v


def test_flatsize(failf=None, stdf=None):
    '''Compare the results of **flatsize()** without using ``sys.getsizeof()``
       with the accurate sizes returned by ``sys.getsizeof()``.

       Return the total number of tests and number of unexpected failures.

       Expect differences for sequences as dicts, lists, sets, tuples, etc.
       While this is no proof for the accuracy of **flatsize()** on Python
       builds without ``sys.getsizeof()``, it does provide some evidence that
       function **flatsize()** produces reasonable and usable results.
    '''
    t, g, e = [], compat._getsizeof, 0
    if g:
        for v in compat._values(type_repo._typedefs):
            t.append(v.type)
            try:  # creating one instance
                if v.type.__module__ not in ('io',):  # avoid 3.0 RuntimeWarning
                    t.append(v.type())
            except (AttributeError, SystemError, TypeError, ValueError):  # ignore errors
                pass
        t.extend(({1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8},
                  [1,2,3,4,5,6,7,8], ['1', '2', '3'], [0] * 100,
                  '12345678', 'x' * 1001,
                  (1,2,3,4,5,6,7,8), ('1', '2', '3'), (0,) * 100,
                  common._Slots((1,2,3,4,5,6,7,8)), common._Slots(('1', '2', '3')), common._Slots((0,) * 100),
                  0, 1 << 8, 1 << 16, 1 << 32, 1 << 64, 1 << 128,
                  complex(0, 1), True, False))
        compat._getsizeof = None  # zap compat._getsizeof for flatsize()
        for o in t:
            a = flatsize(o)
            s = sys.getsizeof(o, 0)  # 0 as default #PYCHOK expected
            if a != s:
                 # flatsize() approximates length of sequences
                 # (sys.getsizeof(bool) on 3.0b3 is not correct)
                if type(o) in (dict, list, set, frozenset, tuple) or (
                   type(o) in (bool,) and sys.version_info[0] == 3):
                    x = ', expected failure'
                else:
                    x = ', %r' % type_spec._typedefof(o)
                    e += 1
                    if failf:  # report failure
                       failf('%s vs %s for %s: %s',
                              a, s, common._nameof(type(o)), common._repr(o))
                if stdf:
                   common._printf('flatsize() %s vs sys.getsizeof() %s for %s: %s%s',
                            a, s, common._nameof(type(o)), common._repr(o), x, file=stdf)
        compat._getsizeof = g  # restore
    return len(t), e


if __name__ == '__main__':

    argv, MAX = sys.argv, sys.getrecursionlimit()

    def _bool(arg):
        a = arg.lower()
        if a in ('1', 't', 'y', 'true', 'yes', 'on'):
            return True
        elif a in ('0', 'f', 'n', 'false', 'no', 'off'):
            return False
        else:
            raise ValueError('bool option expected: %r' % arg)

    def _opts(*_opts, **all):
        for o in _opts:
            if o in argv:
                return True
        o = all.get('all', None)
        if o is None:
            o = '-' in argv or '--' in argv
        return o

    if _opts('-im', '-import', all=False):
         # import and size modules given as args

        def _aopts(argv, **opts):
            '''Get argv options as typed values.
            '''
            i = 1
            while argv[i].startswith('-'):
                k = argv[i].lstrip('-')
                if 'import'.startswith(k):
                    i += 1
                elif k in opts:
                    t = type(opts[k])
                    if t is bool:
                        t = _bool
                    i += 1
                    opts[k] = t(argv[i])
                    i += 1
                else:
                    raise NameError('invalid option: %s' % argv[i])
            return opts, i

        opts, i = _aopts(argv, align=8, clip=80, code=False, derive=False, detail=MAX, limit=MAX, stats=0)
        while i < len(argv):
            m, i = argv[i], i + 1
            if m == 'eval' and i < len(argv):
                o, i = eval(argv[i]), i + 1
            else:
                o = __import__(m)
            s = asizeof(o, **opts)
            common._printf("%sasizeof(%s) is %d", linesep, common._repr(o, opts['clip']), s)
            _print_functions(o, **opts)
        argv = []

    elif len(argv) < 2 or _opts('-h', '-help'):
        d = {'-all':               'all=True example',
             '-basic':             'basic examples',
             '-C':                 'Csizeof values',
             '-class':             'class and instance examples',
             '-code':              'code examples',
             '-dict':              'dict and UserDict examples',
           ##'-gc':                'gc examples',
             '-gen[erator]':       'generator examples',
             '-glob[als]':         'globals examples, incl. asized()',
             '-h[elp]':            'print this information',
             '-im[port] <module>': 'imported module example',
             '-int | -long':       'int and long examples',
             '-iter[ator]':        'iterator examples',
             '-loc[als]':          'locals examples',
             '-pair[s]':           'key pair examples',
             '-slots':             'slots examples',
             '-stack':             'stack examples',
             '-sys':               'sys.modules examples',
             '-test':              'test flatsize() vs sys.getsizeof()',
             '-type[def]s':        'type definitions',
             '- | --':             'all examples'}
        w = -max([len(o) for o in compat._keys(d)])  # [] for Python 2.2
        t = compat._sorted(['%*s -- %s' % (w, o, t) for o, t in compat._items(d)])  # [] for Python 2.2
        t = '\n     '.join([''] + t)
        common._printf('usage: %s <option> ...\n%s\n', argv[0], t)

        class C: pass

        class D(dict):
          _attr1 = None
          _attr2 = None

        class E(D):
          def __init__(self, a1=1, a2=2):  #PYCHOK OK
            self._attr1 = a1  #PYCHOK OK
            self._attr2 = a2  #PYCHOK OK

        class P(object):
          _p = None
          def _get_p(self):
            return self._p
          p = property(_get_p)  #PYCHOK OK

        class O:  # old style
          a = None
          b = None

        class S(object):  # new style
          __slots__ = ('a', 'b')

        class T(object):
          __slots__ = ('a', 'b')
          def __init__(self):
            self.a = self.b = 0

    if _opts('-all'):  # all=True example
        demos.all()
    if _opts('-basic'):  # basic examples
        demos.basic()
    if _opts('-C'):  # show all Csizeof values
      demos.csizes()
    if _opts('-class'):  # class and instance examples
      demos.classes()
    if _opts('-code'):  # code examples
      demos.code()
    if _opts('-dict'):  # dict and UserDict examples
      demos.dict_()
  ##if _opts('-gc'):  # gc examples
      ##common._printf('%sasizeof(limit=%s, code=%s, *%s) ...', linesep, 'MAX', False, 'gc.garbage')
      ##from gc import collect, garbage  # list()
      ##asizeof(limit=MAX, code=False, stats=1, *garbage)
      ##collect()
      ##asizeof(limit=MAX, code=False, stats=2, *garbage)
    if _opts('-gen', '-generator'):  # generator examples
      demos.generator()
    if _opts('-glob', '-globals'):  # globals examples
      demos.globals_()
    if _opts('-int', '-long'):  # int and long examples
      demos.int_long()
    if _opts('-iter', '-iterator'):  # iterator examples
      demos.iter_()
    if _opts('-loc', '-locals'):  # locals examples
      demos.loc()
    if _opts('-pair', '-pairs'):  # key pair examples
      demos.pair()
    if _opts('-slots'):  # slots examples
      demos.slots()
    if _opts('-stack'):  # stack examples
      demos.stack()
    if _opts('-sys'):  # sys.modules examples
      demos.sys_()
    if _opts('-type', '-types', '-typedefs'):  # show all basic _typedefs
      demos.types()
    if _opts('-test'):
      demos.test()


# License file from an earlier version of this source file follows:

#---------------------------------------------------------------------
#       Copyright (c) 2002-2008 -- ProphICy Semiconductor, Inc.
#                        All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# - Neither the name of ProphICy Semiconductor, Inc. nor the names
#   of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
#---------------------------------------------------------------------