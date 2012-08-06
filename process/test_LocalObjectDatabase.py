import unittest

import pickle
import gc

from pickle import dumps, loads

from LocalObjectDatabase import *

from MockProcess import *


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

def loadDB():
    assert MockProcess.current() is not None and MockProcess.current().db is not None
    if MockProcess.current().db:
        return MockProcess.current().db

class TestDB2(LocalObjectDatabase):

    def localProcess(self):
        assert MockProcess.current() is not None
        return MockProcess.current()

    def storeUnderName(self):
        assert MockProcess.current().db is None
        MockProcess.current().db = self

    def getName(self):
        return loadDB, ()

    def delete(self):
        if MockProcess.current():
            MockProcess.current().db = None

    def __str__(self):
        return self.namexxx

class ReferenceTestBase(DatabaseTest):

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

class ReferenceTest(ReferenceTestBase):

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
                self.assertTrue(ref.isDirect())
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
        self.ref1._delete = lambda:None

        
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
            dr._delete = lambda:None

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
            ref._delete = lambda:None
    
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
            ref._delete = lambda:None

class GarbageBase(object):
    def __init__(self):
        self.deleted = False
    def _delete(self):
        self.deleted = True

class IndirectRemoteDatabaseReferenceGarbage(GarbageBase, IndirectRemoteDatabaseReference):
    pass
class DirectDatabaseReferenceGarbage(GarbageBase, RemoteDatabaseReference):
    pass
class LocalDatabaseReferenceGarbage(GarbageBase, LocalDatabaseReference):
    pass


class __del__calls_delete_Test(unittest.TestCase):

    def assertDeletes(self, obj):
        self.assertFalse(obj.deleted)
        obj.__del__()
        self.assertTrue(obj.deleted)

    def test_local(self):
        self.assertDeletes(LocalDatabaseReferenceGarbage())
    def test_direct(self):
        self.assertDeletes(DirectDatabaseReferenceGarbage())
    def test_indirect(self):
        self.assertDeletes(IndirectRemoteDatabaseReferenceGarbage())

class ReferenceTestRaceCondition(ReferenceTestBase):
    '''
we have four processes
process1 : obj
process2 : direct reference
process3 : indirect reference
process4 : indirect reference

if ref4 holds a reference to ref3 and not to the reference to ref3 in process4
the following test should delete this reference first
to simulate a  race condition
This will cause the object to be deleted from the database although
ref4 has the reference
'''

    def four_processes_asynchronous(self):
        s = dumps(self.ref1)
        self.p1.__exit__()
        with self.p2:
            s = dumps(loads(s))
        with self.p3:
            ref3 = loads(s)
            s = dumps(ref3)
        with self.p4:
            ref4 = loads(s)
        with self.p1:
            del self.ref1
        with self.p3:
            ref3.getNewId_()
        with self.p3:
            del ref3
        with self.p4:
            ref4.getNewId_()
            s = dumps(ref4)
        with self.p1:
            ref1 = loads(s)
            self.assertEquals(ref1.value, self.obj)


class IRDR3(IndirectRemoteDatabaseReference):
    getNewIdCalled = False
    def getNewId(self):
        self.getNewIdCalled = True
        IndirectRemoteDatabaseReference.getNewId(self)

    def getNewId_(self):
        assert self.getNewIdCalled
        
class TestDB3(TestDB2):
    IndirectRemoteDatabaseReference = IRDR3


class ReferenceTestRaceCondition_no(ReferenceTestRaceCondition):

    DBClass = TestDB3
    
    def test_four_processes_asynchronous(self):
        self.four_processes_asynchronous()
        

class IRDRDeferred(IndirectRemoteDatabaseReference):
    getNewIdCalled = False
    def getNewId(self):
        self.getNewIdCalled = True

    def getNewId_(self):
        IndirectRemoteDatabaseReference.getNewId(self)
        
class TestDB4(TestDB2):
    IndirectRemoteDatabaseReference = IRDRDeferred

class ReferenceTestRaceCondition_exists(ReferenceTestRaceCondition_no):
    DBClass = TestDB4

class IRDRDeferred_fail(IRDRDeferred):
    def storedLocally(self):
        ref = self.database.newLocalReference()
        ref.value = self ## .reference
        return ref

class RDRDeferred_fail(RemoteDatabaseReference):

    def _delete(self):
        try:
            RemoteDatabaseReference._delete(self)
        except ObjectNotFound:
            pass
        
class TestDB5(TestDB2):
    IndirectRemoteDatabaseReference = IRDRDeferred_fail
    RemoteDatabaseReference = RDRDeferred_fail

class ReferenceTestRaceCondition_exists_fail(ReferenceTestRaceCondition):
    DBClass = TestDB5

    def test_four_processes_asynchronous_with_wrong_references(self):
        self.assertRaises(ObjectNotFound, 
                lambda:self.four_processes_asynchronous())


if __name__ == '__main__':
    t = None # 'ReferenceTestBase.test_indirect_references_not_local'
    unittest.main(defaultTest = t, exit = False, verbosity = 1)

