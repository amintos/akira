import sys
import RemoteException

from thread import start_new_thread, allocate_lock, get_ident
from functools import partial
from types import FunctionType
from Queue import Queue
from proxy import Proxy, insideProxy
from VeryPicklableObject import picklableAttribute
from reference import Result
from threading import RLock

from SelfWrap import use_getattribute


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

class FirstActivity(object):
    def __init__(self, onNewActivity):
        self.onNewActivity = onNewActivity
        self.lock = RLock()
        self.called = False
        
    def nextActivity(self, function):
        with self.lock:
            assert not self.called
            self.called = True
        activity = Activity(self, function)
        self.onNewActivity(activity)
        return activity

class Activity(object):

    def __init__(self, lastActivity, function):
        self.function = function        
        self.last = lastActivity
        self.lock = lastActivity.lock
        self.onNewActivity = lastActivity.onNewActivity
        self.next = None
        self.called = False
        self.notified = False

    def notify(self):
        with self.lock:
            assert not self.notified
            self.notified = True
        self.onNewActivity(self) ## threadsave although not in "with"

    def __call__(self):
        'not threadsave! only call from one thread'
        with self.lock:
            calledBefore = self.called
            assert not calledBefore, 'I shall never be called twice!'
            self.called = True
        try:
            self.function()
        finally:
            with self.lock:
                if self.next:
                    self.next.notify()

    def insertActivity(self, function):
        with self.lock:
            

    def nextActivity(self, function):
        with self.lock:
            assert self.next is None, 'can only have one next activity'
            activity = self.newActivity(self, function)
            self.next = activity
            if self.called:
                self.next.notify()
        return activity

    @property
    def newActivity(self):
        return self.__class__

    def __del__(self):
        if not self.called:
            self()
        

def activeClass(BaseClass, ActivityConstructor = FirstActivity):
    from thread import get_ident as getThreadID

    insideActiveObject = use_getattribute(BaseClass)
    
    class ActiveClass(BaseClass):

        newResult = Result
        
        def __new__(cls, activityQueue, *args, **kw):
            obj = BaseClass.__new__(cls, *args, **kw)
            cls.initActiveObject(obj, activityQueue, ActivityConstructor)
            return obj

        @insideActiveObject
        def initActiveObject(self, activityQueue, ActivityConstructor):
            print 'init', activityQueue, ActivityConstructor
            self.__lastActivity = ActivityConstructor(activityQueue.put)
            self.__threadId = None
            self.__activityQueue = activityQueue
            self.__lock = RLock()

        @insideActiveObject
        def __getattribute__(self, name):
            print '__getattribute__', BaseClass, name
            threadId = getThreadID()
            if self.__threadId == threadId:
                return getattr(self, name)
            return partial(self._createActivity, name)

        @insideActiveObject
        def _createActivity(self, name, *args, **kw):
            print 'create activity', name, args, kw
            result = self.newResult()
            call = partial(self._callMethod, result, name, args, kw)
            with self.__lock:
                newActivity = self.__lastActivity.nextActivity(call)
                self.__lastActivity = newActivity
            return result

        @insideActiveObject
        def _callMethod(self, result, name, args, kw):
            print 'callMethod', name, args, kw
            threadId = getThreadID()
            with self.__lock:
                contextThreadId = self.__threadId
                assert contextThreadId == None or \
                       contextThreadId == threadId, \
                       'can not be executed in two threads'
                self.__threadId = threadId
            try:
                value = getattr(self, name)(*args, **kw)
            except:
                ty, err, tb = RemoteException.exc_info()
                result.setError(ty, err, tb)
            else:
                result.setValue(value)
            finally:
                self.__threadId = contextThreadId
        
    ActiveClass.__name__ = BaseClass.__name__
    ActiveClass.__module__ = BaseClass.__module__
    ActiveClass.insideActiveObject = staticmethod(insideActiveObject)
    return ActiveClass

__all__ = ['ActiveObject', 'ActivityQueue', 'activeClass', 'asExclusiveAccess']
