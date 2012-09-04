import sys
import RemoteException

from thread import start_new_thread, allocate_lock, get_ident
from functools import partial
from types import FunctionType
from Queue import Queue
from proxy import Proxy, insideProxy
from VeryPicklableObject import picklableAttribute
from reference import Result


class ActivityQueue(object):

    # todo: remove timeout and put lambdas into queue

    start_new_thread = staticmethod(start_new_thread)
    
    def __init__(self, threadCount = 0):
        self._runningThreads = set()
        self._dyingThreads = set()
        self._startedThreads = set()
        self._queue = Queue()
        self._lock = allocate_lock()
        self._threadCountToKill = 0
        self.threadCount = threadCount

    @property
    def threadIds(self):
        return (self._runningThreads | self._startedThreads)

    @property
    def threadCount(self):
        with self._lock:
            return len(self.threadIds) - self._threadCountToKill

    @threadCount.setter
    def threadCount(self, value):
        while self.threadCount < value:
            threadId = self.start_new_thread(self.fulfillActivities, ())
            self._startedThreads.add(threadId)
        while self.threadCount > value:
            with self._lock:
                self._threadCountToKill+= 1
            self.put(self._killThread)

    def _killThread(self):
        with self._lock:
            self._dyingThreads.add(get_ident())
            self._threadCountToKill-= 1

    def fulfillActivities(self):
        _id = get_ident()
        try:
            while _id not in self._startedThreads and \
                  _id not in self._dyingThreads:
                self.executeActivity()
            self._runningThreads.add(_id)
            self._startedThreads.discard(_id)
            while _id not in self._dyingThreads:
                self.executeActivity()
        finally:
            self.removeThread(_id)

    def removeThread(self, threadId):
        with self._lock:
            self._dyingThreads.discard(threadId)
            self._runningThreads.discard(threadId)
            self._startedThreads.discard(threadId)

    def executeActivity(self):
        function = self._queue.get()
        function()

    def put(self, activity):
        self._queue.put(activity)

    def active(self, obj):
        return ActiveObject(obj, self)

class Activity(partial):

    def __init__(self, function, reenqueue):
        self.reenqueue = reenqueue
        self.function = function
        self.called = False

    def __call__(self):
        self.called = True
        return self.function()

    def __del__(self):
        if not self.called:
            self.reenqueue(self)


class ActiveObject(Proxy):

    newActivity = Activity

    newResult = Result

    @insideProxy
    def __init__(self, enclosedObject, activityQueue):
        Proxy.__init__(self, enclosedObject)
        self.messageQueue = Queue()
        self.activityQueue = activityQueue
        self.activityLock = allocate_lock()
        self.active = False
        self.activate()

    @insideProxy
    def activate(self):
        with self.activityLock:
            if self.active:
                return
            if self.messageQueue.empty():
                return
            self.activityQueue.put(self.messageQueue.get_nowait())
            self.active = True

    @insideProxy
    def deactivate(self):
        assert self.active, 'If not active I cannot be deactivated!'
        with self.activityLock:
            self.active = False

    @insideProxy
    @picklableAttribute
    def putMessage(self, functionName, *args, **kw):
        result = self.newResult()
        function = partial(self.receiveMessage, functionName, args, kw, result)
        activity = self.newActivity(function, self.reputActivity)
        self.putActivity(activity)
        return result

    @insideProxy
    def putActivity(self, activity):
        self.messageQueue.put(activity)
        self.activate()

    @insideProxy
    def reputActivity(self, activity):
        self.activityQueue.put(activity)

    @insideProxy
    def receiveMessage(self, *args):
        self.evaluateCall(*args)
        self.deactivate()
        self.activate()

    @insideProxy
    def evaluateCall(self, functionName, args, kw, result):
        try:
            value = self.call(functionName, args, kw)
        except:
            ty, err, tb = RemoteException.exc_info()
            result.setError(ty, err, tb)
        else:
            result.setValue(value)

    @insideProxy
    def __getattribute__(self, name):
        if name.startswith('_'):
            return getattr(self, name)
        return partial(self.putMessage, name)

def activeClass(BaseClass, wrap = ActiveObject):
    
    class ActiveClass(BaseClass):
        def __new__(cls, activityQueue, *args, **kw):
            obj = BaseClass.__new__(cls, *args, **kw)
            return activityQueue.active(obj)
        
    ActiveClass.__name__ = BaseClass.__name__
    ActiveClass.__module__ = BaseClass.__module__
    return ActiveClass

__all__ = ['ActiveObject', 'ActivityQueue', 'activeClass']
