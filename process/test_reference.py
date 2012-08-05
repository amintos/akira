from Process import thisProcess
import unittest

from reference import *

class MockReference(object):

    def __init__(self, value):
        self.value = value

    def islocal(self):
        return True

    def localProcess(self):
        return thisProcess

class ProxyTest(unittest.TestCase):

    Proxy = Proxy

    def test_call_of_method(self):
        called = [False]
        def m(*args):
            called[0] = True
        p = self.Proxy(m, MockReference(None))
        self.assertEquals(called, [False])
        meth = p.someMethod
        self.assertEquals(called, [False])
        meth = p.someMethod()
        self.assertEquals(called, [True])


class TestObject(object):

    def setA(self, value):
        self.a = value

    def getA(self):
        return self.a

class TestSend(unittest.TestCase):
    
    def setUp(self):
        pass

if __name__ == '__main__':
    unittest.main(exit = False)
