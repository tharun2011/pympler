 # compatibility functions for more uniform
 # behavior across Python version 2.2 thu 3.0

import sys

def _items(obj):  # dict only
    '''Return iter-/generator, preferably.
    '''
    return getattr(obj, 'iteritems', obj.items)()

def _keys(obj):  # dict only
    '''Return iter-/generator, preferably.
    '''
    return getattr(obj, 'iterkeys', obj.keys)()

def _values(obj):  # dict only
    '''Use iter-/generator, preferably.
    '''
    return getattr(obj, 'itervalues', obj.values)()

try:  # callable() builtin
    _callable = callable
except NameError:  # callable() removed in Python 3.0
    def _callable(obj):
        '''Substitute for callable().'''
        return hasattr(obj, '__call__')

try:  # only used to get the referents of
      # iterators, but gc.get_referents()
      # returns () for dict...-iterators
    from gc import get_referents as _getreferents
except ImportError:
    def _getreferents(unused):
        return ()  # sorry, no refs

 # sys.getsizeof() new in Python 2.6
_getsizeof = getattr(sys, 'getsizeof', None)

try:  # str intern()
    _intern = intern
except NameError:  # no intern() in Python 3.0
    def _intern(val):
        return val

def _kwds(**kwds):  # no dict(key=value, ...) in Python 2.2
    '''Return name=value pairs as keywords dict.
    '''
    return kwds

try:  # sorted() builtin
    _sorted = sorted
except NameError:  # no sorted() in Python 2.2
    def _sorted(vals, reverse=False):
        '''Partial substitute for missing sorted().'''
        vals.sort()
        if reverse:
            vals.reverse()
        return vals

try:  # sum() builtin
    _sum = sum
except NameError:  # no sum() in Python 2.2
    def _sum(vals):
        '''Partial substitute for missing sum().'''
        s = 0
        for v in vals:
            s += v
        return s
