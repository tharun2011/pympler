from os         import linesep
import sys
import weakref  as     Weakref

import asizeof
import common
import compat
import sizes
import type_repo

MAX = sys.getrecursionlimit()

class C: pass

class D(dict):
    _attr1 = None
    _attr2 = None

class E(D):
    def __init__(self, a1=1, a2=2):    #PYCHOK OK
        self._attr1 = a1    #PYCHOK OK
        self._attr2 = a2    #PYCHOK OK

class P(object):
    _p = None
    def _get_p(self):
        return self._p
    p = property(_get_p)    #PYCHOK OK

class O:    # old style
    a = None
    b = None

class S(object):    # new style
    __slots__ = ('a', 'b')

class T(object):
    __slots__ = ('a', 'b')
    def __init__(self):
        self.a = self.b = 0




def _print_asizeof(obj, infer=False, stats=0):
    a = [common._repr(obj),]
    for d, c in ((0, False), (MAX, False), (MAX, True)):
        a.append(asizeof.asizeof(obj, limit=d, code=c, infer=infer, stats=stats))
    common._printf(" asizeof(%s) is %d, %d, %d", *a)

def _print_functions(obj, name=None, align=8, detail=MAX, code=False, limit=MAX,
                                         opt='', **unused):
    if name:
        common._printf('%sasizeof functions for %s ... %s', linesep, name, opt)
    common._printf('%s(): %s', ' basicsize', asizeof.basicsize(obj))
    common._printf('%s(): %s', ' itemsize',    asizeof.itemsize(obj))
    common._printf('%s(): %r', ' leng',            asizeof.leng(obj))
    common._printf('%s(): %s', ' refs',         common._repr(asizeof.refs(obj)))
    common._printf('%s(): %s', ' flatsize',    asizeof.flatsize(obj, align=align))    # , code=code
    common._printf('%s(): %s', ' asized',                     asizeof.asized(obj, align=align, detail=detail, code=code, limit=limit))
    ##common._printf('%s(): %s', '.asized',     _asizer.asized(obj, align=align, detail=detail, code=code, limit=limit))



def all():
    common._printf('%sasizeof(limit=%s, code=%s, %s) ... %s', linesep, 'MAX', True, 'all=True', '-all')
    asizeof.asizeof(limit=MAX, code=True, stats=MAX, all=True)

def basic():
    common._printf('%sasizeof(%s) for (limit, code) in %s ... %s', linesep, '<basic_objects>', '((0, False), (MAX, False), (MAX, True))', '-basic')
    for o in (None, True, False,
                        1.0, 1.0e100, 1024, 1000000000,
                        '', 'a', 'abcdefg',
                        {}, (), []):
        _print_asizeof(o, infer=True)

def csizes():
    t = [t for t in sizes.__dict__.items() if t[0].startswith('_sizeof_')]
    common._printf('%s%d C sizes: (bytes) ... -C', linesep, len(t))
    for n, v in compat._sorted(t):
        common._printf(' sizeof(%s): %r', n[len('_sizeof_'):], v)

def classes():
    common._printf('%sasizeof(%s) for (limit, code) in %s ... %s', linesep, '<non-callable>', '((0, False), (MAX, False), (MAX, True))', '-class')
    for o in (C(), C.__dict__,
                        D(), D.__dict__,
                        E(), E.__dict__,
                        P(), P.__dict__, P.p,
                        O(), O.__dict__,
                        S(), S.__dict__,
                        S(), S.__dict__,
                        T(), T.__dict__):
        _print_asizeof(o, infer=True)

def code():
    common._printf('%sasizeof(%s) for (limit, code) in %s ... %s', linesep, '<callable>', '((0, False), (MAX, False), (MAX, True))', '-code')
    for o in (C, D, E, P, S, T,    # classes are callable
                        type,
                        type_spec._co_refs, type_spec._dict_refs, type_spec._inst_refs, type_spec._len_int, type_spec._seq_refs, lambda x: x,
                        (type_spec._co_refs, type_spec._dict_refs, type_spec._inst_refs, type_spec._len_int, type_spec._seq_refs),
                        type_repo._typedefs):
        _print_asizeof(o)

def dict_():
    common._printf('%sasizeof(%s) for (limit, code) in %s ... %s', linesep, '<Dicts>', '((0, False), (MAX, False), (MAX, True))', '-dict')
    try:
        import UserDict    # no UserDict in 3.0
        for o in (UserDict.IterableUserDict(), UserDict.UserDict()):
            _print_asizeof(o)
    except ImportError:
        pass

    class _Dict(dict):
        pass

    for o in (dict(), _Dict(),
                        P.__dict__,    # dictproxy
                        Weakref.WeakKeyDictionary(), Weakref.WeakValueDictionary(),
                        type_repo._typedefs):
        _print_asizeof(o, infer=True)

def generator():
    common._printf('%sasizeof(%s, code=%s) ... %s', linesep, '<generator>', True, '-gen[erator]')
    def gen(x):
        i = 0
        while i < x:
            yield i
            i += 1
    a = gen(5)
    b = gen(50)
    asizeof.asizeof(a, code=True, stats=1)
    asizeof.asizeof(b, code=True, stats=1)
    asizeof.asizeof(a, code=True, stats=1)

def globals_():
    common._printf('%sasizeof(%s, limit=%s, code=%s) ... %s', linesep, 'globals()', 'MAX', False, '-glob[als]')
    asizeof.asizeof(globals(), limit=MAX, code=False, stats=1)
    _print_functions(globals(), 'globals()', opt='-glob[als]')

    common._printf('%sasizesof(%s, limit=%s, code=%s) ... %s', linesep, 'globals(), locals()', 'MAX', False, '-glob[als]')
    asizeof.asizeof(globals(), locals(), limit=MAX, code=False, stats=1)
    asizeof.asized(globals(), align=0, detail=MAX, limit=MAX, code=False, stats=1)

def int_long():
    try:
        _L5d    = long(1) << 64
        _L17d = long(1) << 256
        t = '<int>/<long>'
    except NameError:
        _L5d    = 1 << 64
        _L17d = 1 << 256
        t = '<int>'

    common._printf('%sasizeof(%s, align=%s, limit=%s) ... %s', linesep, t, 0, 0, '-int')
    for o in (1024, 1000000000,
                        1.0, 1.0e100, 1024, 1000000000,
                        MAX, 1 << 32, _L5d, -_L5d, _L17d, -_L17d):
        common._printf(" asizeof(%s) is %s (%s + %s * %s)", common._repr(o), asizeof.asizeof(o, align=0, limit=0),
                                     asizeof.basicsize(o), asizeof.leng(o), asizeof.itemsize(o))

def iter_():
    common._printf('%sasizeof(%s, code=%s) ... %s', linesep, '<iterator>', False, '-iter[ator]')
    o = iter('0123456789')
    e = iter('')
    d = iter({})
    i = iter(compat._items({1:1}))
    k = iter(compat._keys({2:2, 3:3}))
    v = iter(compat._values({4:4, 5:5, 6:6}))
    l = iter([])
    t = iter(())
    asizeof.asizesof(o, e, d, i, k, v, l, t, limit=0, code=False, stats=1)
    asizeof.asizesof(o, e, d, i, k, v, l, t, limit=9, code=False, stats=1)

def loc():
    common._printf('%sasizeof(%s, limit=%s, code=%s) ... %s', linesep, 'locals()', 'MAX', False, '-loc[als]')
    asizeof.asizeof(locals(), limit=MAX, code=False, stats=1)
    _print_functions(locals(), 'locals()', opt='-loc[als]')

def pair():
    # <http://jjinux.blogspot.com/2008/08/python-memory-conservation-tip.html>
    common._printf('%sasizeof(%s) vs asizeof(%s) ... %s', linesep, 'dict[i][j]', 'dict[(i,j)]', '-pair[s]')
    n = m = 200

    p = {}    # [i][j]
    for i in range(n):
        q = {}
        for j in range(m):
            q[j] = None
        p[i] = q
    p = asizeof.asizeof(p, stats=1)

    t = {}    # [(i,j)]
    for i in range(n):
        for j in range(m):
            t[(i,j)] = None
    t = asizeof.asizeof(t, stats=1)

    common._printf('%sasizeof(dict[i][j]) is %s of asizeof(dict[(i,j)])', linesep, asizeof._p100(p, t))

def slots():
    common._printf('%sasizeof(%s, code=%s) ... %s', linesep, '<__slots__>', False, '-slots')
    class Old:
        pass    # m = None
    class New(object):
        __slots__ = ('n',)
    class Sub(New):    #PYCHOK OK
        __slots__ = {'s': ''}    # duplicate!
        def __init__(self):    #PYCHOK OK
            New.__init__(self)
    # basic instance sizes
    o, n, s = Old(), New(), Sub()
    asizeof.asizesof(o, n, s, limit=MAX, code=False, stats=1)
    # with unique min attr size
    o.o = 'o'
    n.n = 'n'
    s.n = 'S'
    s.s = 's'
    asizeof.asizesof(o, n, s, limit=MAX, code=False, stats=1)
    # with duplicate, intern'ed, 1-char string attrs
    o.o = 'x'
    n.n = 'x'
    s.n = 'x'
    s.s = 'x'
    asizeof.asizesof(o, n, s, 'x', limit=MAX, code=False, stats=1)
    # with larger attr size
    o.o = 'o'*1000
    n.n = 'n'*1000
    s.n = 'n'*1000
    s.s = 's'*1000
    asizeof.asizesof(o, n, s, 'x'*1000, limit=MAX, code=False, stats=1)

def stack():
    common._printf('%sasizeof(%s, limit=%s, code=%s) ... %s', linesep, 'stack(MAX)', 'MAX', False, '')
    asizeof.asizeof(asizeof.stack(MAX), limit=MAX, code=False, stats=1)
    _print_functions(asizeof.stack(MAX), 'stack(MAX)', opt='-stack')

def sys_():
    common._printf('%sasizeof(limit=%s, code=%s, *%s) ... %s', linesep, 'MAX', False, 'sys.modules.values()', '-sys')
    asizeof.asizeof(limit=MAX, code=False, stats=1, *sys.modules.values())
    _print_functions(sys.modules, 'sys.modules', opt='-sys')

def types():
    t = len(type_repo._typedefs)
    w = len(str(t)) * ' '
    common._printf('%s%d type definitions: basic- and itemsize (leng), kind ... %s', linesep, t, '-type[def]s')
    for k, v in compat._sorted([(asizeof._prepr(k), v) for k, v in compat._items(type_repo._typedefs)]):    # [] for Python 2.2
        s = '%(base)s and %(item)s%(leng)s, %(kind)s%(code)s' % v.format()
        common._printf('%s %s: %s', w, k, s)

def test():
    common._printf('%sflatsize() vs sys.getsizeof() ... %s', linesep, '-test')
    n, e = asizeof.test_flatsize(stdf=sys.stdout)
    if e:
        common._printf('%s%d of %d tests failed or %s', linesep, e, n, _p100(e, n))
    elif compat._getsizeof:
        common._printf('no unexpected failures in %d tests', n)
    else:
        common._printf('no sys.%s() in this python %s', 'getsizeof', sys.version.split()[0])
