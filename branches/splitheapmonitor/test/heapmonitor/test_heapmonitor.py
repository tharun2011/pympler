import unittest
import gc
import re
try:
    from StringIO import StringIO
    BytesIO = StringIO
except ImportError:
    from io import StringIO, BytesIO

from pympler.heapmonitor.heapmonitor import *
import pympler.process

class Foo:
    def __init__(self):
        self.foo = 'foo'

class Bar(Foo):
    def __init__(self):
        Foo.__init__(self)
        self.bar = 'bar'

class FooNew(object):
    def __init__(self):
        self.foo = 'foo'

class BarNew(FooNew):
    def __init__(self):
        super(BarNew, self).__init__()


class TrackObjectTestCase(unittest.TestCase):

    def setUp(self):
        detach_all()

    def test_track_object(self):
        """Test object registration.
        """
        foo = Foo()
        bar = Bar()

        track_object(foo)
        track_object(bar)

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

        assert 'Foo' in tracked_index
        assert 'Bar' in tracked_index

        assert tracked_objects[id(foo)].ref() == foo
        assert tracked_objects[id(bar)].ref() == bar

    def test_type_errors(self):
        """Test intrackable objects.
        """
        i = 42
        j = 'Foobar'
        k = [i,j]
        l = {i: j}

        self.assertRaises(TypeError, track_object, i)
        self.assertRaises(TypeError, track_object, j)
        self.assertRaises(TypeError, track_object, k)
        self.assertRaises(TypeError, track_object, l)

        assert id(i) not in tracked_objects
        assert id(j) not in tracked_objects
        assert id(k) not in tracked_objects
        assert id(l) not in tracked_objects

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        foo = Foo()

        track_object(foo, name='Foobar')

        assert 'Foobar' in tracked_index        
        assert tracked_index['Foobar'][0].ref() == foo

    def test_keep(self):
        """Test lifetime of tracked objects.
        """
        foo = Foo()
        bar = Bar()

        track_object(foo, keep=1)
        track_object(bar)
       
        idfoo = id(foo)
        idbar = id(bar)

        del foo
        del bar

        assert tracked_objects[idfoo].ref() is not None
        assert tracked_objects[idbar].ref() is None

    def test_mixed_tracking(self):
        """Test mixed instance and class tracking.
        """
        f = StringIO()
        foo = Foo()
        track_object(foo)
        create_snapshot()
        print_stats(fobj=f)
        track_class(Foo)
        objs = []
        for _ in range(10):
            objs.append(Foo())
        create_snapshot()
        print_stats(fobj=f)

    def test_recurse(self):
        """Test recursive sizing and saving of referents.
        """
        foo = Foo()

        track_object(foo, resolution_level=1)
        create_snapshot()

        fp = tracked_objects[id(foo)].footprint[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        assert len(dref) == 1
        dref = dref[0]
        assert dref.size > 0
        assert dref.flat > 0
        assert dref.refs == ()

        # Test track_change and more fine-grained resolution
        track_change(foo, resolution_level=2)
        create_snapshot()

        fp = tracked_objects[id(foo)].footprint[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        assert len(dref) == 1
        dref = dref[0]
        namerefs = [r.name for r in dref.refs]
        assert '[K] foo' in namerefs
        assert "[V] foo: 'foo'" in namerefs        

class SnapshotTestCase(unittest.TestCase):

    def setUp(self):
        clear()

    def tearDown(self):
        stop_periodic_snapshots()

    def test_timestamp(self):
        """Test timestamp of snapshots.
        """
        foo = Foo()
        bar = Bar()

        track_object(foo)
        track_object(bar)

        create_snapshot()
        create_snapshot()
        create_snapshot()

        refts = [fp.timestamp for fp in footprint]
        for to in tracked_objects.values():
            ts = [t for (t,sz) in to.footprint[1:]]
            assert ts == refts

    def test_snapshot_members(self):
        """Test existence and value of snapshot members.
        """
        foo = Foo()
        track_object(foo)
        create_snapshot()

        fp = footprint[0]
        assert fp.overhead > 0
        assert fp.tracked_total > 0
        assert fp.asizeof_total > 0
        assert fp.asizeof_total >= fp.tracked_total

        if pympler.process.is_available():
            assert fp.system_total.vsz > 0
            assert fp.system_total.rss > 0
            assert fp.system_total.vsz >= fp.system_total.rss 
            assert fp.system_total.vsz > fp.overhead
            assert fp.system_total.vsz > fp.tracked_total
            assert fp.system_total.vsz > fp.asizeof_total

    def test_desc(self):
        """Test footprint description.
        """
        create_snapshot()
        create_snapshot('alpha')
        create_snapshot(description='beta')
        create_snapshot(42)

        assert len(footprint) == 4
        assert footprint[0].desc == ''
        assert footprint[1].desc == 'alpha'
        assert footprint[2].desc == 'beta'
        assert footprint[3].desc == '42'

    def test_background_monitoring(self):
        """Test background monitoring.
        """
        import pympler.heapmonitor
        import time

        start_periodic_snapshots(0.1)
        assert pympler.heapmonitor._periodic_thread.interval == 0.1
        assert pympler.heapmonitor._periodic_thread.getName() == 'BackgroundMonitor'
        for x in range(10): # try to interfere
            create_snapshot(str(x))
        time.sleep(0.5)
        start_periodic_snapshots(0.2)
        assert pympler.heapmonitor._periodic_thread.interval == 0.2
        stop_periodic_snapshots()
        assert pympler.heapmonitor._periodic_thread is None
        assert len(footprint) > 10


class TrackClassTestCase(unittest.TestCase):

    def setUp(self):
        detach_all()

    def test_track_class(self):
        """Test tracking objects through classes.
        """
        track_class(Foo)
        track_class(Bar)

        foo = Foo()
        bar = Bar()

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

    def test_track_class_new(self):
        """Test tracking new style classes.
        """
        track_class(FooNew)
        track_class(BarNew)

        foo = FooNew()
        bar = BarNew()

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        track_class(Foo, name='Foobar')

        foo = Foo()

        assert 'Foobar' in tracked_index        
        assert tracked_index['Foobar'][0].ref() == foo

    def test_keep(self):
        """Test lifetime of tracked objects.
        """
        track_class(Foo, keep=1)
        track_class(Bar)

        foo = Foo()
        bar = Bar()
       
        idfoo = id(foo)
        idbar = id(bar)

        del foo
        del bar

        assert tracked_objects[idfoo].ref() is not None
        assert tracked_objects[idbar].ref() is None

    def test_detach(self):
        """Test detaching from tracked classes.
        """
        track_class(Foo)
        track_class(Bar)

        foo = Foo()
        bar = Bar()

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

        detach_class(Foo)
        detach_class(Bar)

        foo2 = Foo()
        bar2 = Bar()
    
        assert id(foo2) not in tracked_objects
        assert id(bar2) not in tracked_objects

        self.assertRaises(KeyError, detach_class, Foo)

    def test_change_name(self):
        """Test modifying name.
        """
        track_class(Foo, name='Foobar')
        track_class(Foo, name='Baz')
        foo = Foo()

        assert 'Foobar' not in tracked_index
        assert 'Baz' in tracked_index
        assert tracked_index['Baz'][0].ref() == foo

class LogTestCase(unittest.TestCase):

    def setUp(self):
        detach_all()

    def test_dump(self):
        """Test serialization of log data.
        """
        foo = Foo()
        foo.data = range(1000)
        bar = Bar()

        track_object(foo, resolution_level=4)
        track_object(bar)

        create_snapshot('Footest')

        f1 = StringIO()
        f2 = StringIO()

        print_stats(fobj=f1)

        tmp = BytesIO()
        dump_stats(tmp, close=0)

        clear()

        stats = MemStats(stream=f2)
        assert stats.tracked_index is None
        assert stats.footprint is None
        tmp.seek(0)
        stats.load_stats(tmp)
        tmp.close()
        assert 'Foo' in stats.tracked_index

        stats.print_stats()
        stats.print_summary()

        assert f1.getvalue() == f2.getvalue()

        # Test sort_stats and reverse_order
        assert stats.sort_stats('size') == stats
        assert stats.sorted[0].classname == 'Foo'
        stats.reverse_order()
        assert stats.sorted[0].classname == 'Bar'
        stats.sort_stats('classname', 'birth')
        assert stats.sorted[0].classname == 'Bar'
        self.assertRaises(ValueError, stats.sort_stats, 'name', 42, 'classn')
        assert stats.diff_stats(stats) == None # Not yet implemented

        # Test partial printing
        stats.stream = f3 = StringIO()
        stats.sort_stats()
        tolen = len(stats.sorted)
        stats.print_stats(filter='Bar',limit=0.5)
        assert len(stats.sorted) == tolen
        stats.print_summary()
        clsname = f3.getvalue().split(' ')[0]
        assert re.search('.Bar', clsname) != None, clsname
        assert len(f3.getvalue()) < len(f1.getvalue())

        f1.close()
        f2.close()
        f3.close()


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ TrackObjectTestCase,
                 TrackClassTestCase,
                 SnapshotTestCase,
                 LogTestCase
               ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)