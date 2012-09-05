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
        return self.function(self)

    def __del__(self):
        if not self.called:
            self.reenqueue(self)
        
class ActiveAttribute(object):

    def __init__(self, function):
        self.function = function

    def __call__(self, activeObject, result, args, kw):
        return self.function(activeObject, result, args, kw)


def activeClass(BaseClass, ActivityConstructor = FirstActivity):
    from thread import get_ident as getThreadID

    insideActiveObject = use_getattribute(BaseClass)
    
    class ActiveClass(BaseClass):

        newResult = Result
        newActivity = Activity

        directAccess = ('__reduce__', '__reduce_ex__', '__enter__', '__exit__')

        #
        # methods using the lock
        #

        @insideActiveObject
        def __enter__(self):
            assert self.__lock.acquire(False), 'used by an other thread'

        @insideActiveObject
        def __exit__(self, *args):
            self.__lock.release()

        def __init__(self, *args, **kw):
            with self:
                BaseClass.__init__(self, *args, **kw)

        @insideActiveObject
        def enqueueActivity(self):
            with self:
                assert self.__activityWaitingToBeFulfilled is None
                activity = self.activities.pop(0)
                self.__activityWaitingToBeFulfilled = activity
            self.__activityQueue.put(activity)

        @insideActiveObject
        def appendActivity(self, function):
            activity = self.newActivity(function, self.reenqueueActivity)
            with self.__lock:
                self.activities.append(activity)
            self.notifyAboutActivities()

        @insideActiveObject
        def injectActivity(self, function):
            activity = self.newActivity(activity, self.reenqueueActivity))
            with self.__lock:
                self.activities.insert(0, activity)
            self.notifyAboutActivities()

        @insideActiveObject
        def reenqueueActivity(self, activity):
            if self.__deleted:
                return 
            assert activity is self.__activityWaitingToBeFulfilled
            with self.__lock:
                self.__activityWaitingToBeFulfilled = None
                self.injectActivity(activity)

        @insideActiveObject
        def notifyAboutActivities(self):
            with self.__lock:
                if not self.__activityWaitingToBeFulfilled and self.activities:
                    self.enqueueActivity()
                
        @insideActiveObject
        def _fulfillActivity(self, name, args, kw, result, activity):
            print 'callMethod', name, args, kw
            assert self.__activityWaitingToBeFulfilled is activity, \
                   'can not fulfill an activity out of order'
            try:
                attribute = getattr(self, name)
                if issubclass(type(attribute), ActiveAttribute):
                    attribute(self, args, kw, result)
                else:
                    self._callMethod(attribute, args, kw)
            finally:
                self.__activityWaitingToBeFulfilled = None
                self.notifyAboutActivities()

        @insideActiveObject
        def __getattribute__(self, name):
            print '__getattribute__', BaseClass, name
            if self.__lock._is_owned():
                return getattr(self, name)
            if name in self.directAccess:
                return getattr(self, name)
            return partial(self._createActivity, name)

        #
        # methods NOT using the lock
        #

        def __new__(cls, activityQueue, *args, **kw):
            obj = BaseClass.__new__(cls, *args, **kw)
            cls.initActiveObject(obj, activityQueue, ActivityConstructor)
            return obj

        @insideActiveObject
        def initActiveObject(self, activityQueue, ActivityConstructor):
            print 'init', activityQueue, ActivityConstructor
            self.activities = []
            self.__lock = RLock()
            self.__activityQueue = activityQueue
            self.__activityWaitingToBeFulfilled = None
            self.__deleted = False

        @insideActiveObject
        def _callMethod(self, attribute, args, kw)
            try:
                value = attribute(*args, **kw)
            except:
                ty, err, tb = RemoteException.exc_info()
                result.setError(ty, err, tb)
            else:
                result.setValue(value)

        @insideActiveObject
        def _createActivity(self, name, *args, **kw):
            print 'create activity', name, args, kw
            result = self.newResult()
            call = partial(self._fulfillActivity, name, args, kw, result)
            self.appendActivity(call)
            return result

        @insideActiveObject
        def __del__(self):
            self.__deleted = True

        
    ActiveClass.__name__ = BaseClass.__name__
    ActiveClass.__module__ = BaseClass.__module__
    ActiveClass.insideActiveObject = staticmethod(insideActiveObject)
    return ActiveClass

__all__ = ['ActiveObject', 'ActivityQueue', 'activeClass', 'asExclusiveAccess']
