#!/usr/bin/env python
from struct     import calcsize  # type/class Struct only in Python 2.5+
import sys

 # sizes of some primitive C types
 # XXX len(pack(T, 0)) == Struct(T).size == calcsize(T)
_sizeof_Cbyte  = calcsize('c')  # sizeof(unsigned char)
_sizeof_Clong  = calcsize('l')  # sizeof(long)
_sizeof_Cvoidp = calcsize('P')  # sizeof(void*)

def _calcsize(fmt):
    '''struct.calcsize() handling 'z' for Py_ssize_t.
    '''
     # sizeof(long) != sizeof(ssize_t) on LLP64
    if _sizeof_Clong < _sizeof_Cvoidp:
        z = 'P'
    else:
        z = 'L'
    return calcsize(fmt.replace('z', z))

_sizeof_Cdouble  = _calcsize('d')  #PYCHOK OK
_sizeof_Cssize_t = _calcsize('z')  #PYCHOK OK

 # defaults for some basic sizes with 'z' for C Py_ssize_t
_sizeof_CPyCodeObject   = _calcsize('Pz10P5i0P')    # sizeof(PyCodeObject)
_sizeof_CPyFrameObject  = _calcsize('Pzz13P63i0P')  # sizeof(PyFrameObject)
_sizeof_CPyModuleObject = _calcsize('PzP0P')        # sizeof(PyModuleObject)

 # defaults for some item sizes with 'z' for C Py_ssize_t
_sizeof_CPyDictEntry    = _calcsize('z2P')  # sizeof(PyDictEntry)
_sizeof_Csetentry       = _calcsize('lP')   # sizeof(setentry)

try:  # C typedef digit for multi-precision int (or long)
    _sizeof_Cdigit = long.__itemsize__
except NameError:  # no long in Python 3.0
    _sizeof_Cdigit = int.__itemsize__
if _sizeof_Cdigit < 2:
    raise AssertionError('sizeof(%s) bad: %d' % ('digit', _sizeof_Cdigit))

try:  # sizeof(unicode_char)
    u = unicode('\0')
except NameError:  # no unicode() in Python 3.0
    u = '\0'
u = u.encode('unicode-internal')  # see .../Lib/test/test_sys.py
_sizeof_Cunicode = len(u)
del u
if sys.maxunicode >= (1 << (_sizeof_Cunicode << 3)):
    raise AssertionError('sizeof(%s) bad: %d' % ('unicode', _sizeof_Cunicode))

try:  # size of GC header, sizeof(PyGC_Head)
    import _testcapi as t
    _sizeof_CPyGC_Head = t.SIZEOF_PYGC_HEAD  # new in Python 2.6
except (ImportError, AttributeError):  # sizeof(PyGC_Head)
     # alignment should be to sizeof(long double) but there
     # is no way to obtain that value, assume twice double
    t = calcsize('2d') - 1
    _sizeof_CPyGC_Head = (_calcsize('2Pz') + t) & ~t
del t

 # size of refcounts (Python debug build only)
if hasattr(sys, 'gettotalrefcount'):
    _sizeof_Crefcounts = _calcsize('2z')
else:
    _sizeof_Crefcounts =  0
