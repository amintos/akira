import sys
import time
import unittest

from functools import partial
from multiprocessing.pool import Pool
from LocalObjectDatabase import LocalObjectDatabase
from StringIO import StringIO
from pickle import loads, dumps, PicklingError, UnpicklingError

from Process import thisProcess
from test_multi_Process import timeout, TIMEOUT
from reference import *


class MockReference(object):
    process = None

    def __init__(self, value):
        self.value = value

    def isLocal(self):
        return True

    def localProcess(self):
        return thisProcess

    def isMockReference(self):
        return True

class ProxyTest(unittest.TestCase):
    maxDiff = None

    Proxy = ReferenceProxy

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

    def test_pass_args_to_method(self):
        l = []
        obj = X()
        obj.process = None
        obj.isLocal = None
        def method(*args, **kw):
            l.append((args, kw))

        p = self.Proxy(method, obj)
        p.append(3,4, a = '3')
        t = l[0]
        self.assertEquals(t[1], {})
        args = t[0]
        self.assertEquals(args[1], '__call__')
        self.assertEquals(args[2], (3,4))
        self.assertEquals(args[3], {'a':'3'})


    def test_add(self):
        p = self.Proxy(sync, ref(1))
        self.assertEquals(p + 1, 2)


    class X(object): ## todo: test with oldstyle
        a = 1
        def f():pass
        __reduce__ = __reduce_ex__ = 1

    def test_attributes_are_the_same_plus_exceptions(self):
        self.assertDir(self.X())

    def assert_class_objects_can_be_listed(self):
        self.assertDir(self.X)

    def assertDir(self, o):
        l = dir(o)
        l.sort()
        p = self.Proxy(sync, ref(o))
        l2 = dir(p)
        l2.sort()
        self.assertEquals(l2, l)
        

class TestObject(object):

    def setA(self, value):
        self.a = value

    def getA(self):
        return self.a

thisProcess.listenOnIPv4()

def g():
    pass

class DB(LocalObjectDatabase):
    pass

db = DB()

def setValue(*args):
    global value
    value = args

value = None

class MyError(Exception):
    pass

ref = db.store
class X(object):

    def __init__(self):
        self.value = None
        self._start = 'wait'

    def setValue(self, newValue):
        self.value = newValue
        return 'valueSet'

    def setValueWithError(self, value):
        self.setValue(value)
        raise MyError('error!')

    def setValue_wait_delete(self, value, after = None):
        self.setValue(value)
        self.wait()
        self.setValue(after)
        return (value, after)

    def start(self):
        self._start = 'start'
        
    def wait(self):
        timeout(lambda: self._start, 'wait')
        if self._start != 'start':
            raise MyError('timed out')

class TestBase(unittest.TestCase):
    '''this test is based on the LocalObjectDatabase and multi_process

the tests execute send, sync, async, ...
from another process to local references of this process.
'''
    @classmethod
    def setUpClass(cls):
        cls.pool = Pool(1)
        cls.pool.apply_async(thisProcess.call, (g, ())).get(TIMEOUT)
        timeout(lambda:thisProcess.knownProcesses, set())

    @classmethod
    def tearDownClass(cls):
##        cls.pool.close()
##        cls.pool.join()
        pass

    def setUp(self):
        global value
        self.x = x = X()
        x.setValue(None)
        self.ref = ref(x)
        value = None
        

class SendTest(TestBase):
    
    def test_setValue(self):
        x = self.x
        v = self.pool.apply_async(send, (self.ref, 'setValue', \
                                         (5,), {}))
        timeout(lambda: x.value, None)
        self.assertEquals(x.value, 5)
        self.assertEquals(v.get(), None) # sometimes race-condition

    def test_send_and_error(self):
        x = self.x
        stderr, sys.stderr = sys.stderr, StringIO()
        try:
            v = self.pool.apply_async(send, (self.ref, 'setValueWithError', \
                                             ('error',), {}))
            timeout(lambda: x.value, None)
        finally:
            time.sleep(0.1)
            sys.stderr, stderr = stderr, sys.stderr
        self.assertEquals(x.value, 'error')
        self.assertNotEquals(stderr.getvalue(), '')

def _call_async(*args):
    v = async(*args)
    try:
        return v.get(TIMEOUT)
    except:
        return sys.exc_info()[:2]
    
def async_do(*args):
    async(*args)
    return 'done'

class AsyncTest(TestBase):

    def test_real_async_with_wait(self):
        v = self.pool.apply_async(async_do, (self.ref, 'setValue_wait_delete', \
                                             ('aValue',), {'after':2}))
        self.assertEquals(v.get(TIMEOUT), 'done')
        timeout(lambda: self.x.value, None)
        self.assertEquals(self.x.value, 'aValue')
        self.x.start()
        timeout(lambda: self.x.value, 'aValue')
        self.assertEquals(self.x.value, 2)
        

    def test_setValue(self):
        v = self.pool.apply_async(_call_async, (self.ref, 'setValue', \
                                                ('aValue',), {})).get(TIMEOUT)
        self.assertEquals(v, 'valueSet')
        self.assertEquals(self.x.value, 'aValue')

##    def test_send_error(self):
##        ## error - all is dead
##        try: raise
##        except: ty, err, tb = sys.exc_info()
##        self.pool.apply_async(getattr, (tb, 'tb_next', None)).get(TIMEOUT)

    def test_setValue_error(self):
        v = self.pool.apply_async(_call_async, (self.ref, 'setValueWithError', \
                                          ('aValue',), {}))
        v = v.get(TIMEOUT * 2)
        self.assertEquals(v[0], MyError)
        self.assertEquals(v[1].args, ('error!',))
        self.assertEquals(self.x.value, 'aValue')

class SomeError(Exception):
    pass

def _sync_call_error(*args):
    try:
        sync(*args)
    except:
        return sys.exc_info()[:2]
    return (SomeError, SomeError('exeption not raised'))

class SyncTest(TestBase):

    def test_wait(self):
        x = self.x
        v = self.pool.apply_async(sync, (self.ref, 'setValue_wait_delete', \
                                         ('sen_d',), {'after':3}))
        timeout(lambda:x.value, None)
        self.assertEquals(x.value, 'sen_d')
        time.sleep(0.01)
        self.assertEquals(x.value, 'sen_d')
        timeout(lambda:v.ready(), True)
        self.assertFalse(v.ready())
        x.start()
        timeout(lambda:x.value, 'sen_d')
        self.assertEquals(x.value, 3)
        self.assertEquals(v.get(1), ('sen_d', 3))

    def test_error(self):
        v = self.pool.apply_async(_sync_call_error, \
                                        (self.ref, 'setValueWithError', \
                                        ('lalala',), {}))
        v = v.get(TIMEOUT)
        self.assertEquals(self.x.value, 'lalala')
        self.assertEquals(v[0], MyError)
        self.assertEquals(v[1].args, ('error!',))

    pass

def callback_test(*args):
    callback(*args)
    return 'value!'

class CallbackTest(TestBase):

    def test_send_partial(self):
         cb = partial(thisProcess.call, setValue)
         cb((1,))
         self.assertEquals(value, (1,))
         self.pool.apply_async(cb, ((2,),)).get(TIMEOUT)
         timeout(lambda: value, (1,))
         self.assertEquals(value, (2,))
         
    def test_wait(self):
        x = self.x
        cb = partial(thisProcess.call, setValue)
        v = self.pool.apply_async(callback_test, (self.ref, \
                                         'setValue_wait_delete', \
                                         (cb, 's',), {'after':3}))
        self.assertEquals(v.get(TIMEOUT), 'value!')
        timeout(lambda: x.value, None)
        self.assertEquals(x.value, 's')
        self.assertNotEqual(value, ('s', 3))
        x.start()
        timeout(lambda: x.value, 's')
        self.assertEquals(x.value, 3)
        timeout(lambda: value, None)
        self.assertEqual(value, ('s', 3))

class ReferenceTest(unittest.TestCase):
    

    def test_sync(self):
        obj = []
        p = reference(obj, sync)
        p.append(3)
        self.assertEquals(obj, [3])

    def test_exchangeMethod(self):
        p = reference([], sync)
        self.assertEquals(referenceMethod(p), sync)
        p2 = reference(p, async)
        self.assertIsNot(p2, p)
        self.assertEquals(referenceMethod(p2), async)
 
    def test_reduce(self):
        l = []
        class X(object):
            @staticmethod
            def xx(a):
                l.append(a)
                return a * a
        p = reference(X, sync)
        s = dumps(p)
        p2 = loads(s)
        value = p2.xx(3)
        self.assertEquals(value, 9)
        self.assertEquals(l, [3])
    
class AttributeReferenceTest(unittest.TestCase):

    def test_pickle_mock_reference(self):
        s = dumps(MockReference(1))
        l = loads(s)
        self.assertTrue(l.isMockReference())

    def test_value(self):
        l = []
        m = MockReference(l)
        ref = AttributeReference(m, 'append')
        self.assertEquals(ref.value, l.append)
        
    def test_reduce(self):
        l = []
        self.assertRaises(Exception,
                          lambda: dumps(l.append))
        m = ref(l)
        ar = AttributeReference(m, 'append')
        s = dumps(ar)
        ar2 = loads(s)
        self.assertEquals(ar2.value, l.append)
        self.assertNotEquals(ar2.value, list().append)


class ReferenceMultiProcessTest(TestBase):

    def test_append_to_list(self):
        l = []
        r = reference(l, sync)
        none = self.pool.apply(r.append, (4,))
        self.assertEquals(none, None)
        
    def test_pop_from_list(self):
        l = [4]
        r = reference(l, sync)
        four = self.pool.apply(r.pop, ())
        self.assertEquals(four, 4)

    @unittest.skip('this is not the duty of a reference')
    def test_dir_list_from_other_side(self):
        l1 = functionsOf([])
        r = self.pool.apply(reference, ([], sync))
        l2 = functionOf(r)
        print l1, l2,
        self.assertEquals(l1, l2)

    def test_pickle_reference(self):
        s = dumps((reference, ([], sync)))
        l = loads(s)
        self.assertEquals(l, (reference, ([], sync)))

    @unittest.skip('todo or not?')
    def test_class_of_list_reference_is_list(self):
        r = self.pool.apply(reference, ([], sync))
        self.assertEquals(r.__class__, list)
    
##
#### for dir()

class M(type):
    def __getattribute__(self, name):
        print 'type', name
        v = type.__getattribute__(self, name)
        print v
        print
        return v

class Y(object):
    __metaclass__ = M
    def __getattribute__(self, name):
        print name
        v = object.__getattribute__(self, name)
        print v
        print
        return v


    
if __name__ == '__maind__':
    import thread
    defaultTest = 'AsyncTest.test_setValue_error'
    kw = dict(defaultTest = defaultTest, exit = False, verbosity = 2)
    unittest.main(**kw)
##    _id = thread.start_new(unittest.main, (), kw)
