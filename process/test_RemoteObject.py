import unittest

import pickle
from Process import thisProcess
from RemoteObject import storeObject, loadObject, freeObject, ObjectNotFound
from RemoteObject import *
from proxy import insideProxy
import gc


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

class ReferenceTest(unittest.TestCase):

    def setUp(self):
        obj =  []
        ref = onlyInThisProcess(obj)
        self.ref = ref
        self.obj = obj
        self.setProcess(self.ref, MockProcess())

    def setProcess(self, ref, process):
        @insideProxy
        def g(ref):
            ref.process = process
        g(ref)

    def getId(self, reference):
        @insideProxy
        def h(reference):
            return reference.id
        return h(reference)

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
        ref3 = dumpLoad(dumpLoad(dumpLoad(ref2)))
        id2 = self.getId(ref2)
        id3 = self.getId(ref3)
        self.assertNotEqual(id3, id2)
        _id = self.getId(ref2)
        del ref2
        gc.collect()
        self.assertRaises(ObjectNotFound, lambda: loadObject(_id))
        ref3.append(4)
        self.assertEquals(self.obj, [4])
        

if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
