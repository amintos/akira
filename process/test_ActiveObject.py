import unittest

from Queue import Queue
from ActiveObject import *

from test_multi_Process import timeout
from functools import partial

class ActiveObjectTest(unittest.TestCase):

    def setUp(self):
        self.queue = Queue()
        self.obj = set()
        self.a = ActiveObject(self.obj, self.queue)

    def test_call_is_not_executed(self):
        self.assertNotIn(3, self.obj)
        self.a.add(3)
        self.assertNotIn(3, self.obj)

    def test_call_is_in_queue(self):
        self.a.add(3)
        self.queue.get_nowait()()
        self.assertIn(3, self.obj)

    def test_two_calls_are_in_order(self):
        self.a.add(1)
        self.a.add(2)
        c1 = self.queue.get_nowait()
        self.assertTrue(self.queue.empty())
        c1()
        self.assertEquals(self.obj, set([1]))
        c2 = self.queue.get_nowait()
        c2()
        self.assertEquals(self.obj, set([1, 2]))

    def test_when_activity_is_deleted_it_is_enqueued_if_not_executed(self):
        self.a.add(1)
        self.a.add(2)
        c1 = self.queue.get_nowait()
        c1.__del__()
        c1 = self.queue.get_nowait()
        c1()
        self.assertEquals(self.obj, set([1]))

    def test_call_activity_then_delete(self):
        self.a.add(1)
        self.a.add(2)
        c = self.queue.get_nowait()
        c()
        c.__del__()
        c = self.queue.get_nowait()
        c()
        self.assertEquals(self.obj, set([1, 2]))

    def test_result(self):
        self.obj.add(1)
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

    def appendToList(self, l, e):
        l.append(e)

    def appendInside(self, l, e):
        l2 = []
        assert e not in l2
        self.appendToList(l2, e)
        assert e in l2
        self.appendToList(l, e)
        return e

    @asExclusiveAccess
    def waitForOtherActor(self, callback, other, value):
        l = []
        v = yield other.appendInside(l, value)
        assert v is value
        callback(v + v)

class MyActiveObjectTest(unittest.TestCase):

    def setUp(self):
        self.pool = ActivityQueue(1)
        self.a = MyActiveObject(self.pool)

    def tearDown(self):
        self.pool.threadCount = 0        

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

class DeferredMessageSendTest(unittest.TestCase):

    def setUp(self):
        self.queue = Queue()
        self.a = MyActiveObject(self.queue)
        self.b = MyActiveObject(self.queue)

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

    def test_waitForOtherActor(self):
        self.a.waitForOtherActor()

    
if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
    import sys
    if not 'idlelib' in sys.modules:
        raw_input()
