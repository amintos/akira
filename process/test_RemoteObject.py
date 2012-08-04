import unittest

import pickle
from Process import thisProcess
from RemoteObject import storeObject, loadObject, freeObject, ObjectNotFound
from RemoteObject import *
from proxy import insideProxy
import gc

import RemoteObject as RemoteObjectModule


class DatabaseTest(unittest.TestCase):

    def test_can_store_object(self):
        l = [[] for l in range(20)]
        ids = []
        for obj in l:
            ids.append(storeObject(obj))
        for i, obj in enumerate(l):
            self.assertIs(loadObject(ids[i]), obj)


    def test_invalid_id(self):
        self.assertRaises(ObjectNotFound, lambda: loadObject('23423423423'))

    def test_too_high_id(self):
        self.assertRaises(ObjectNotFound, lambda: loadObject(storeObject(1) + 132312))

    def test_free_object(self):
        id1 = storeObject([1])
        id2 = storeObject([2])
        freeObject(id2)
        self.assertEquals(loadObject(id1), [1])
        self.assertRaises(ObjectNotFound, lambda: loadObject(id2))

def dumpLoad(obj):
    return pickle.loads(pickle.dumps(obj))

class MockProcess(object):

    def call(self, *args):
        return apply(*args)

    def mock(self):
        return True

class AsynMockProcess(object):
    instances = []

    def __init__(self):
        self.calls = []

    def call(self, *args):
        self.calls.append(args)

    def do(self):
        while self.calls:
            apply(*self.calls.pop())

_local_LocalObject = RemoteObjectModule.LocalObject
class LocalObject2(_local_LocalObject):
    @insideProxy
    def __init__(self, enclosedObject, process = None):
        assert process is None
        _local_LocalObject.__init__(self, enclosedObject, MockProcess())
    

class ReferenceTestBase(unittest.TestCase):
    
    def setUp(self):
        self.original = RemoteObjectModule.LocalObject
        RemoteObjectModule.LocalObject = LocalObject2
        obj =  []
        ref = onlyInThisProcess(obj)
        self.ref = ref
        self.obj = obj
        self.setProcess(self.ref, MockProcess())

    def tearDown(self):
        RemoteObjectModule.LocalObject = self.original

    def setProcess(self, ref, process):
        @insideProxy
        def g(ref):
            ref.process = process
        g(ref)

    def getProcess(self, ref, process):
        @insideProxy
        def g(ref):
            return ref.process
        return g(ref)

    def getId(self, reference):
        @insideProxy
        def h(reference):
            return reference.id
        return h(reference)

    def aquireId(self, ref):
        pass


class ReferenceTest(ReferenceTestBase):

    def test_directreference(self):
        self.ref.append(1)
        self.assertIsNot(self.ref, self.obj)
        self.assertEquals(obj, [1])

    def test_directreference(self):
        ref2 = dumpLoad(self.ref)
        self.setProcess(ref2, thisProcess)
        ref2.append(1)
        self.assertIsNot(ref2, self.obj)
        self.assertEquals(self.obj, [1])

    def test_two_mockProcesses_are_not_equal(self):
        self.assertNotEqual(MockProcess(), MockProcess())

    def test_reference_dies(self):
        ref2 = dumpLoad(self.ref)
        _id = self.getId(ref2)
        self.assertIs(loadObject(_id), self.obj)
        del ref2
        self.assertRaises(ObjectNotFound, lambda: loadObject(_id))

    def test_mockprocess_is_pickled(self):
        ref2 = dumpLoad(self.ref)
        self.assertTrue(object.__getattribute__(ref2, 'process').mock())
        
    def test_indirect_references_get_new_id(self):
        ref2 = dumpLoad(self.ref)
        ref3 = dumpLoad(ref2)
        id2 = self.getId(ref2)
        id3 = self.getId(ref3)
        self.assertNotEqual(id3, id2)
        _id = self.getId(ref2)
        del ref2
        gc.collect()
        self.assertNotEqual(self.getId(ref3), _id)
        self.assertRaises(ObjectNotFound, lambda: loadObject(_id))
        ref3.append(4)
        self.assertEquals(self.obj, [4])

DirectRemoteReference1 = RemoteObjectModule.DirectRemoteReference
class DirectRemoteReference2(DirectRemoteReference1):

    @insideProxy
    def getSelfReference(self):
        self.proxy = None
        return DirectRemoteReference1.getSelfReference(self)

IndirectRemoteReference1 = RemoteObjectModule.IndirectRemoteReference
class IndirectRemoteReference2(IndirectRemoteReference1, DirectRemoteReference2):

    exceptions = IndirectRemoteReference1.exceptions + ('acquireNewId_',)
    proxyToNone  = False
    @insideProxy
    def getSelfReference(self):
##        print 'getSelfReference', repr(self.proxy), self.proxyToNone
        if self.proxyToNone:
##            self.proxy_ = self.proxy # do not drop the reference
            self.proxy = None
        return IndirectRemoteReference1.getSelfReference(self)

    @insideProxy
    def acquireNewId(self):
        pass

    acquireNewId_ = IndirectRemoteReference1.acquireNewId


    @insideProxy
    def setId(self, newId):
        IndirectRemoteReference1.setId(self, newId)
        self._proxy = None


class ReferenceTestSpecialCaseBase(ReferenceTestBase):
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
    proxyToNone = 1
    def setUp(self):
        IndirectRemoteReference2.proxyToNone = self.proxyToNone
        RemoteObjectModule.IndirectRemoteReference = IndirectRemoteReference2
        RemoteObjectModule.DirectRemoteReference = DirectRemoteReference2
        ReferenceTestBase.setUp(self)

    def test_reduce_is_equal(self):
        self.assertEquals(IndirectRemoteReference2.__reduce__, \
                          IndirectRemoteReference1.__reduce__,)
        

    def four_processes_asynchronous(self):
##        print '-' * 50
        ref1 = self.ref
##        print 'ref1:', repr(ref1)
        del self.ref
        ref2 = dumpLoad(ref1)
##        print 'ref2:', repr(ref2)
        ref3 = dumpLoad(ref2)
##        print 'ref3:', repr(ref3)
        ref4 = dumpLoad(ref3)
##        print 'ref4:', repr(ref4)

        del ref1
##        print 'acquire ref3'
        ref3.acquireNewId_()
##        print gc.get_referrers(ref2)
        del ref2
##        print 'acquire ref4'
        ref4.acquireNewId_()
        ref4.append(4)
        self.assertEquals(self.obj, [4])

    def tearDown(self):
        ReferenceTestBase.tearDown(self)
        RemoteObjectModule.IndirectRemoteReference = IndirectRemoteReference1
        RemoteObjectModule.DirectRemoteReference = DirectRemoteReference1
            

##del ReferenceTest, DatabaseTest
class ReferenceTestSpecialCaseFail(ReferenceTestSpecialCaseBase):

    proxyToNone = True
    
    def test_four_processes_asynchronous_with_wrong_references(self):
        self.assertRaises(ObjectNotFound, 
                lambda:self.four_processes_asynchronous())
            
        
class ReferenceTestSpecialCaseWorks(ReferenceTestSpecialCaseBase):

    proxyToNone = False
    
    def test_four_processes_asynchronous(self):
        self.four_processes_asynchronous()
        
        

if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
