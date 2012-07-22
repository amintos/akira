import unittest
import proxy


class X(object):
    pass

class ProxyAttributeTest(unittest.TestCase):

    def setUp(self):
        self.object = X()
        self.proxy = proxy.proxy(self.object)

    def test_get_a(self):
        self.object.a = 1
        self.assertEquals(self.proxy.a, 1)

    def test_get_b_from_object(self):
        self.proxy.b = 4
        self.assertEquals(self.object.b, 4)

    def test_get_and_set(self):
        self.proxy.c = 0
        self.assertEquals(self.proxy.c, 0)

    def test_add_something(self):
        self.proxy.a = 3
        self.proxy.a += 4
        self.assertEquals(self.proxy.a, 7)

    def test_hash(self):
        self.assertEquals(hash(self.proxy), hash(self.object))


class _CallProxy(proxy.Proxy):

    def isLocal(self):
        return False

    @proxy.insideProxy
    def call(self, *args):
        return self.enclosedObject(*args)
    

class MethodCallTest(unittest.TestCase):

    def setUp(self):
        self.lastCalled = None
        def call(methodName, args, kw):
            self.lastCalled = methodName, args, kw
            return self.proxy
        self.proxy = _CallProxy(call)

    def assertLastCalled(self, methodName, *args, **kw):
        self.assertEquals((methodName, args, kw), self.lastCalled)

    def test_someMethod(self):
        self.proxy.someMethod(1,2,3,4)
        self.assertLastCalled('__call__', 1,2,3,4)

    def test_add(self):
        self.proxy + 2
        self.assertLastCalled('__add__', 2)

    def test_getSomething(self):
        self.assertIs(self.proxy.x, self.proxy)
        self.assertLastCalled('__getattribute__', 'x')


if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
