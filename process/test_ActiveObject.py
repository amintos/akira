import unittest

from Queue import Queue
from ActiveObject import *

from test_multi_Process import timeout
from functools import partial

class ActiveObjectTest(unittest.TestCase):

    def setUp(self):
        self.queue = Queue()
        self.a = activeClass(set)(self.queue)

    def test_call_is_not_executed(self):
        self.assertNotIn(3, self.a)
        self.a.add(3)
        self.assertNotIn(3, self.a)

    def test_call_is_in_queue(self):
        self.a.add(3)
        self.queue.get_nowait()()
        self.assertIn(3, self.a)

    def test_two_calls_are_in_order(self):
        self.a.add(1)
        self.a.add(2)
        c1 = self.queue.get_nowait()
        self.assertTrue(self.queue.empty())
        c1()
        self.assertEquals(self.a, set([1]))
        c2 = self.queue.get_nowait()
        c2()
        self.assertEquals(self.a, set([1, 2]))

    def test_when_activity_is_deleted_it_is_enqueued_if_not_executed(self):
        self.a.add(1)
        self.a.add(2)
        c1 = self.queue.get_nowait()
        c1.__del__()
        c1 = self.queue.get_nowait()
        c1()
        self.assertEquals(self.a, set([1]))

    def test_call_activity_then_delete(self):
        self.a.add(1)
        self.a.add(2)
        c = self.queue.get_nowait()
        c()
        c.__del__()
        c = self.queue.get_nowait()
        c()
        self.assertEquals(self.a, set([1, 2]))

    def test_result(self):
        self.a.add(1)
        c = self.queue.get_nowait()
        c()
        r = self.a.pop()
        self.assertFalse(r.ready())
        self.queue.get_nowait()()
        self.assertTrue(r.ready())
        self.assertEquals(r.get(), 1)

    def test_result_error(self):
        r = self.a.ahgjhgjhsfgkjhsdfjk(1)
        self.queue.get_nowait()()
        self.assertTrue(r.ready())
        self.assertRaises(AttributeError, lambda: r.get())

    def test_outside_is_object(self):
        self.assertIs(self.a.active, self.a)


r = iter(xrange(10000))
class MockActivityQueue1(ActivityQueue):
    start_new_thread = lambda self, func, args: next(r)


class MockActivityQueue2(ActivityQueue):
    removed = 0
    def start_new_thread(self, *args):
        import thread
        self.wait = True
        _id = thread.start_new_thread(*args)
        timeout(lambda: self.wait, True)
        return _id

    def executeActivity(self):
        self.wait = False
        ActivityQueue.executeActivity(self)

    def removeThread(self, _id):
        ActivityQueue.removeThread(self, _id)
        self.removed+= 1

class ActivityQueueTest(unittest.TestCase):

    def test_set_thread_count(self):
        aq = MockActivityQueue1()
        aq.threadCount = 3
        self.assertEquals(aq.threadCount, 3)
        self.assertEquals(len(aq._startedThreads), 3)
        self.assertEquals(len(aq._runningThreads), 0)
        self.assertEquals(len(aq._dyingThreads), 0)

    def test_remove_threads(self):
        threadCount = 3
        aq = MockActivityQueue2()
        l = []
        aq.threadCount = threadCount
        self.assertEquals(len(aq.threadIds), threadCount)
        for i in range(threadCount):
            ref = aq.removed
            aq.threadCount -= 1
            self.assertEquals(aq.threadCount, threadCount - i - 1)
            timeout(lambda: aq.removed, ref)
            self.assertEquals(aq.removed, ref + 1)
        self.assertEquals(aq.removed, threadCount)

@activeClass
class MyActiveObject(object):

    def __init__(self, x):
        self.x = x

    def appendToList(self, l, e):
        l.append(e)

    def appendInside(self, l, e):
        l2 = []
        assert e not in l2
        self.appendToList(l2, e)
        assert e in l2
        self.appendToList(l, e)
        return e

    @stepByStep
    def waitForOtherActor(self, callback, other, value):
        l = []
        v = yield other.appendInside(l, value)
        assert v is value
        callback(v + v)

class DeferredMessageSendTest(unittest.TestCase):

    def setUp(self):
        self.queue = Queue()
        self.a = MyActiveObject(self.queue, None)
        self.b = MyActiveObject(self.queue, None)

    def executeCall(self):
        c = self.queue.get_nowait()
        c()

    def test_append_to_list(self):
        l = []
        self.a.appendToList(l, 3)
        self.executeCall()
        self.assertEquals(l, [3])
        
    def test_call_inside_is_executed_inside(self):
        l = []
        self.a.appendInside(l, 3)
        self.executeCall()
        self.assertEquals(l, [3])

    @unittest.skip('this has to be implemented in future')
    def test_waitForOtherActor(self):
        v = self.a.waitForOtherActor(self.b, 'hallo')
        self.executeCall()
        self.executeCall()
        self.executeCall()
        self.assertTrue(v.ready())
        self.assertEquals(v.get(), 'hallo' * 2)
        
        
class MyActiveObjectTest(unittest.TestCase):

    def setUp(self):
        self.pool = ActivityQueue(1)
        self.x = []
        self.a = MyActiveObject(self.pool, self.x)

    def tearDown(self):
        self.pool.threadCount = 0

    def test_init_gets_no_queue(self):
        with self.a:
            self.assertEquals(self.a.x, self.x)

    def test_append_to_list(self):
        l = []
        self.a.appendToList(l, 3)
        timeout(lambda:l, [])
        self.assertEquals(l, [3])

    def test_append_to_list_inside(self):
        l = []
        self.a.appendInside(l, 3)
        timeout(lambda:l, [])
        self.assertEquals(l, [3])


## todo: reference tests multi-process
    
if __name__ == '__main__':
    dT = None
##    dT = 'DeferredMessageSendTest.test_call_inside_is_executed_inside'
    unittest.main(defaultTest = dT, exit = False, verbosity = 1)
##    import sys
##    if not 'idlelib' in sys.modules:
##        raw_input()
