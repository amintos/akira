from functools import partial
import sys
import time

from Process import thisProcess
import unittest

from test_multi_Process import timeout, TIMEOUT
from reference import *

from multiprocessing.pool import Pool

from LocalObjectDatabase import LocalObjectDatabase

from StringIO import StringIO

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
        print 'close'
        cls.pool.close()
        print 'closed'
        cls.pool.join()
        print 'joined'

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
        v = v.get(TIMEOUT)
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
         timeout(lambda: value, None)
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


##del SendTest
##del SyncTest
##del CallbackTest
##del AsyncTest
        
if __name__ == '__main__':
    import thread
    defaultTest = None#'SyncTest.test_wait'#None#'AsyncTest.test_real_async_with_wait'
    kw = dict(defaultTest = defaultTest, exit = False, verbosity = 2)
    unittest.main(**kw)
##    _id = thread.start_new(unittest.main, (), kw)
