import unittest

import pickle
import gc

from pickle import dumps, loads

from LocalObjectDatabase import *

class TestDatabase1(LocalObjectDatabase):
    pass

class DatabaseTest(unittest.TestCase):

    DBClass = TestDatabase1

    def setUp(self):
        self.db = self.DBClass()

    def tearDown(self):
        self.db.delete()

    def test_no2db_can_exist(self):
        self.assertRaises(AssertionError, lambda: self.DBClass())

    def test_can_store_object(self):
        db = self.db
        l = [[] for l in range(20)]
        refs = []
        for obj in l:
            refs.append(db.store(obj))
        for i, obj in enumerate(l):
            self.assertIs(refs[i].value, obj)


    def test_invalid_id(self):
        _id = '23423423423'
        self.assertRaises(ObjectNotFound, lambda: self.db.loadObjectById(_id))

    def test_too_high_id(self):
        _id = self.db.store(1).id + 132312
        self.assertRaises(ObjectNotFound, lambda: self.db.loadObjectById(_id))

    def test_free_object(self):
        ref1 = self.db.store([1])
        ref2 = self.db.store([2])
        self.db.freeObjectById(ref2.id)
        self.assertEquals(self.db.loadObjectById(ref1.id), [1])
        self.assertRaises(ObjectNotFound, lambda: \
                          self.db.loadObjectById(ref2.id))
        self.db.storeObjectToId([], ref2.id)


    def test_pickle_db(self):
        self.assertIs(dl(self.db), self.db)

    def test_duplicateObjectById(self):
        ref = self.db.store([2,2,2])
        _id = self.db.duplicateObjectById(ref.id)
        self.assertTrue(self.db.hasObjectById(_id))
        self.assertEquals(self.db.loadObjectById(_id), [2,2,2])

def dl(obj):
    import pickle
    return pickle.loads(pickle.dumps(obj))

from R import R

proc = None
class MockProcess(object):

    proc = {}

    def __init__(self, name):
        self.proc.setdefault(name, self)
        self.name = name
        self.db = None
        self.local = False

    def isThisProcess(self):
        return self.local

    def call(self, *args):
##        print 'dump -->'
        s = dumps(R(args))
##        print '<-- dump'
        def g():
            with self.proc[self.name]:
                ## use the original process
##                print 'load -->'
                loads(s)
##                print '<-- load'
        self.without(g)
        

    def __enter__(self):
        global proc
##        print 'enter', proc, self
        assert proc is None or proc is self
        proc = self
        self.local = True

    def __reduce__(self):
        return loadProc, (self.name,)

    def __exit__(self, *args):
##        print 'exit', self
        self.local = False
        global proc
        proc = None

    def isMock(self): return True

    def without(self, func):
        _proc = proc
        _proc.__exit__()
        try:
            return func()
        finally:
            _proc.__enter__()

    @classmethod
    def reset(cls):
        global proc
        proc = None
        cls.proc = {}

    def __repr__(self):
        return 'MP[%s]' % (self.name,)

    def __eq__(self, other):
        return self.name == other.name


class MockInOtherProcess(MockProcess):
    def __repr__(self):
        return 'MIOP[%s]' % (self.name,)


MockProcess.MockInOtherProcess = MockInOtherProcess

def loadProc(name):
    assert proc is not None
    if name == proc.name:
        return proc
    l = proc.MockInOtherProcess
    return proc.without(lambda: l(name))

def loadDB():
    assert proc is not None and proc.db is not None
    if proc.db:
        return proc.db

class TestDB2(LocalObjectDatabase):

    def localProcess(self):
        assert proc is not None
        return proc

    def storeUnderName(self):
        assert proc.db is None
        proc.db = self

    def getName(self):
        return loadDB, ()

    def delete(self):
        if proc:
            proc.db = None

    def __str__(self):
        return self.namexxx

class LocalDatabaseReference2(LocalDatabaseReference):
    deleted = False
    def _delete(self):
        self.deleted = True    

class IndirectRemoteDatabaseReference2(IndirectRemoteDatabaseReference):
    deleted = False
    def _delete(self):
        self.deleted = True
    
class RemoteDatabaseReference2(RemoteDatabaseReference):
    deleted = False
    def _delete(self):
        self.deleted = True



class ReferenceTest(DatabaseTest):

    DBClass = TestDB2

    def MockInOtherProcess(self, name):
        return self.MockProcess(name, MockInOtherProcess)

    def MockProcess(self, name, cls = MockProcess):
        p = cls(name)
        MockProcess.MockInOtherProcess = self.MockInOtherProcess
        with p:
            db = self.DBClass()
            db.namexxx = 'DB{%s}' % name
        return p

    def setUp(self):
        MockProcess.reset()
        self.p1 = self.MockProcess('p1')
        self.p2 = self.MockProcess('p2')
        self.p3 = self.MockProcess('p3')
        self.p4 = self.MockProcess('p4')
        with self.p1:
            self.p1.db = None
            DatabaseTest.setUp(self)
            self.db.namexxx = 'DB1'
            self.obj = []
            self.ref1 = self.db.store(self.obj)
        self.p1.__enter__()

    def tearDown(self):
        DatabaseTest.tearDown(self)
        self.p1.__exit__()

    def test_ref_process_is_mocked(self):
        self.assertTrue(self.ref1.process.isMock())
    
    def test_ref_process_is_context(self):
        self.p1.__exit__()
        with self.p2:
            ref = dl(self.ref1)
            self.assertEquals(ref.process.name, self.p1.name)
            self.assertIsNot(ref.process, self.p1)
    
    def test_local_reference_local(self):
        with self.p1:
            ref = dl(self.ref1)
            self.assertIs(ref.process, self.p1)
            self.assertTrue(ref.process.isThisProcess())
            self.assertTrue(ref.isLocal())
            self.assertTrue(self.db.hasObjectById(ref.id), ref.id)

    def test_direct_references_not_local(self):
        self.p1.__exit__()
        with self.p2:
            dr = dl(self.ref1)
            self.assertFalse(dr.process.isThisProcess())
            self.assertFalse(dr.isLocal())
            self.assertTrue(self.db.hasObjectById(dr.id), dr.id)

##    @unittest.skip('later')
    def test_indirect_references_not_local(self):
        s = dumps(self.ref1)
        self.p1.__exit__()
        with self.p2:
##            print '-----in p2-----'
            dr = loads(s)
            s = dumps(dr)
        with self.p3:
##            print '-----in p3-----'
            ir = loads(s)
            self.assertFalse(ir.process.isThisProcess())
            self.assertFalse(ir.isLocal())
            self.assertTrue(self.db.hasObjectById(ir.id), ir.id)

    def test_direct_reference_becomes_local_again(self):
        s = dumps(self.ref1)
        self.p1.__exit__()
        with self.p2:
            dr = loads(s)
            self.assertFalse(dr.isLocal())
            s = dumps(dr)
        with self.p1:
            ref = loads(s)
            self.assertTrue(ref.isLocal())
        

    def test_pickle_databases(self):
        for db in (self.p1.db, self.p2.db, self.p3.db, self.p4.db, ):
            for p in (self.p1, self.p2, self.p3, self.p4):
                with p:
                    self.assertIs(dl(db), p.db)


    def test_process_in_with_statement_is_local(self):
        self.p1.__exit__()
        self.assertFalse(self.p3.isThisProcess())
        with self.p3:
            self.assertTrue(self.p3.isThisProcess())
        self.assertFalse(self.p3.isThisProcess())

    def test_reduce_4_times(self):
        s = dumps(self.ref1)
        _id = self.ref1.id
        self.p1.__exit__()
        for i in range(50):
            p = self.MockProcess('Proc%s' % i)
            with p:
                ref = loads(s)
                self.assertGreater(ref.id, _id)
                _id = ref.id
                s = dumps(ref)
        with self.p1:
            ref = loads(s)
            self.assertTrue(ref.isLocal())
            self.assertIs(self.ref1.value, self.obj)
            self.assertIs(self.ref1.value, self.obj)

    def test_garbage_collect_local(self):
        self.ref1._delete()
        self.assertRaises(ObjectNotFound, lambda: self.ref1.value)
        
    def test_garbage_collect_remote(self):
        s = dumps(self.ref1)
        self.p1.__exit__()
        with self.p2:
            dr = loads(s)
            self.assertIs(self.db.loadObjectById(dr.id), self.obj)
            _id = dr.id
            dr._delete()
            self.assertRaises(ObjectNotFound, lambda: \
                              self.db.loadObjectById(_id))

    def test_garbage_collect_indirect(self):
        s = dumps(self.ref1)
        self.p1.__exit__()
        with self.p2:
            s = dumps(loads(s))
        with self.p3:
            ref = loads(s)
            self.assertIs(self.db.loadObjectById(ref.id), self.obj)
            _id = ref.id
            ref._delete()
            self.assertRaises(ObjectNotFound, lambda: \
                              self.db.loadObjectById(_id))
    
    def test_garbage_collect_indirect2(self):
        s = dumps(self.ref1)
        self.p1.__exit__()
        with self.p2:
            s = dumps(loads(s))
        with self.p4:
            s = dumps(loads(s))
        with self.p3:
            ref = loads(s)
            self.assertIs(self.db.loadObjectById(ref.id), self.obj)
            _id = ref.id
            ref._delete()
            self.assertRaises(ObjectNotFound, lambda: \
                              self.db.loadObjectById(_id))
    
if __name__ == '__main__':
    t = None # 'ReferenceTestBase.test_indirect_references_not_local'
    unittest.main(defaultTest = t, exit = False, verbosity = 1)

