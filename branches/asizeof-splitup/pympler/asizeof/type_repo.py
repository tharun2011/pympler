from inspect    import isbuiltin, isclass, iscode, isframe, isfunction, ismethod, ismodule
import types    as     Types

import common
import compat
import sizes
import type_common

 # kinds of _Typedefs
_i = compat._intern
_all_kinds = (_kind_static, _kind_dynamic, _kind_derived, _kind_ignored, _kind_inferred) = (
                _i('static'), _i('dynamic'), _i('derived'), _i('ignored'), _i('inferred'))
del _i



_typedefs = {}  # [key] = _Typedef()

# TODO(schuppe): modified in type_spec.py
_dict_classes = {}
# TODO(schuppe): modified in type_spec.py
_dict_typedef = {}
# TODO(schuppe): modified in type_spec.py
_all_refs = ()
# TODO(schuppe): modified in type_spec.py
_all_lengs = ()



class _Typedef(object):
    '''Type definition class.
    '''
    __slots__ = {
        'base': 0,     # basic size in bytes
        'item': 0,     # item size in bytes
        'leng': None,  # or type_spec._len_...() function
        'refs': None,  # or _..._refs() function
        'both': None,  # both data and code if True, code only if False
        'kind': None,  # _kind_... value
        'type': None}  # original type

    def __init__(self, **kwds):
        self.reset(**kwds)

    def __lt__(self, unused):  # for Python 3.0
        return True

    def __repr__(self):
        return repr(self.args())

    def __str__(self):
        t = [str(self.base), str(self.item)]
        for f in (self.leng, self.refs):
            if f:
                t.append(f.__name__)
            else:
                t.append('n/a')
        if not self.both:
            t.append('(code only)')
        return ', '.join(t)

    def args(self):  # as args tuple
        '''Return all attributes as arguments tuple.
        '''
        return (self.base, self.item, self.leng, self.refs,
                self.both, self.kind, self.type)

    def dup(self, other=None, **kwds):
        '''Duplicate attributes of dict or other typedef.
        '''
        if other is None:
            d = _dict_typedef.kwds()
        else:
            d =  other.kwds()
        d.update(kwds)
        self.reset(**d)

    def flat(self, obj, mask=0):
        '''Return the aligned flat size.
        '''
        s = self.base
        if self.leng and self.item > 0:  # include items
            s += self.leng(obj) * self.item
        if compat._getsizeof:  # _getsizeof prevails
            s = compat._getsizeof(obj, s)
        if mask:  # align
            s = (s + mask) & ~mask
        return s

    def format(self):
        '''Return format dict.
        '''
        c = n = ''
        if not self.both:
            c = ' (code only)'
        if self.leng:
            n = ' (%s)' % common._nameof(self.leng)
        return compat._kwds(base=self.base, item=self.item, leng=n,
                     code=c,         kind=self.kind)

    def kwds(self):
        '''Return all attributes as keywords dict.
        '''
         # no dict(refs=self.refs, ..., kind=self.kind) in Python 2.0
        return compat._kwds(base=self.base, item=self.item,
                     leng=self.leng, refs=self.refs,
                     both=self.both, kind=self.kind, type=self.type)

    def save(self, t, base=0, heap=False):
        '''Save this typedef plus its class typedef.
        '''
        c, k = type_common._keytuple(t)
        if k and k not in _typedefs:  # instance key
            _typedefs[k] = self
            if c and c not in _typedefs:  # class key
                if t.__module__ in common._builtin_modules:
                    k = _kind_ignored  # default
                else:
                    k = self.kind
                _typedefs[c] = _Typedef(base=common._basicsize(type(t), base=base, heap=heap),
                                        refs=type_common._type_refs,
                                        both=False, kind=k, type=t)
        elif isbuiltin(t) and t not in _typedefs:  # array, range, xrange in Python 2.x
            _typedefs[t] = _Typedef(base=common._basicsize(t, base=base),
                                    both=False, kind=_kind_ignored, type=t)
        else:
            raise KeyError('asizeof typedef %r bad: %r %r' % (self, (c, k), self.both))

    def set(self, safe_len=False, **kwds):
        '''Set one or more attributes.
        '''
        if kwds:  # double check
            d = self.kwds()
            d.update(kwds)
            self.reset(**d)
        if safe_len and self.item:
            self.leng = type_common._len

    def reset(self, base=0, item=0, leng=None, refs=None,
                                    both=True, kind=None, type=None):
        '''Reset all specified attributes.
        '''
        if base < 0:
            raise ValueError('invalid option: %s=%r' % ('base', base))
        else:
            self.base = base
        if item < 0:
            raise ValueError('invalid option: %s=%r' % ('item', item))
        else:
            self.item = item
        if leng in _all_lengs:  # XXX or compat._callable(leng)
            self.leng = leng
        else:
            raise ValueError('invalid option: %s=%r' % ('leng', leng))
        if refs in _all_refs:  # XXX or compat._callable(refs)
            self.refs = refs
        else:
            raise ValueError('invalid option: %s=%r' % ('refs', refs))
        if both in (False, True):
            self.both = both
        else:
            raise ValueError('invalid option: %s=%r' % ('both', both))
        if kind in _all_kinds:
            self.kind = kind
        else:
            raise ValueError('invalid option: %s=%r' % ('kind', kind))
        self.type = type



def _typedef_both(t, base=0, item=0, leng=None, refs=None, kind=_kind_static, heap=False):
    '''Add new typedef for both data and code.
    '''
    v = _Typedef(base=common._basicsize(t, base=base), item=common._itemsize(t, item),
                 refs=refs, leng=leng,
                 both=True, kind=kind, type=t)
    v.save(t, base=base, heap=heap)
    return v  # for _dict_typedef

def _typedef_code(t, base=0, refs=None, kind=_kind_static, heap=False):
    '''Add new typedef for code only.
    '''
    v = _Typedef(base=common._basicsize(t, base=base),
                 refs=refs,
                 both=False, kind=kind, type=t)
    v.save(t, base=base, heap=heap)
    return v  # for _dict_typedef
