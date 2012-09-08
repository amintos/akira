import socket
import time
import thread
import os
import Queue
import threading
from R import R

from VeryPicklableObject import picklableAttribute
import Listener
from setConnectionEndpointsAlgorithm import setConnectionEndpoints
from markAsDeadAlgorithm import markAsDead

_cachedProcesses = {}
_cachedProcessesLock = thread.allocate_lock()

class ProcessCannotConnect(Listener.ConnectionBroken):
    pass

class ProcessIsDead(ProcessCannotConnect):
    pass

def getProcess(identityString, ProcessClass, args = (), kw = {}):
    assert isinstance(identityString, basestring), 'The identity must be a string'
    with _cachedProcessesLock:
        process = _cachedProcesses.get(identityString, None)
        if process is None:
            process = ProcessClass(*args, **kw)
            _cachedProcesses[identityString] = process
    return process

class Process(object):
    def __init__(self, identityString, pid, hostName, creationTime,
                 listeners = []):
        assert isinstance(identityString, basestring), 'The identity must be a string'
        self.__identityString = identityString
        self.pid = pid
        self.hostName = hostName
        self.creationTime = creationTime

    @property
    def identityString(self):
        return self.__identityString

    @picklableAttribute
    def call(self, aFunction, args, kw = {}):
        raise NotImplementedError('todo')    
    
    def __reduce__(self):
        return self.getLoadFunction(), \
                (self.identityString, self.ProcessClassAfterUnpickling,
                 (self.identityString, self.pid, self.hostName,
                  self.creationTime),)

    def getLoadFunction(self):
        '=> function to use to load process after transfer over aConnections'
        return getProcess

    def __eq__(self, other):
        return getattr(other, 'isProcess', lambda:False)() and \
               self.identityString == other.identityString

    def __hash__(self):
        return hash(self.identityString)

    def __le__(self, other):
        return self.creationTime < other.creationTime

    def thisProcess(self):
        return thisProcess

    def isThisProcess(self):
        return self.thisProcess() is self

    def isProcess(self):
        return True

    def __str__(self):
        return 'Process %s on %s' % (self.pid, self.hostName)

Process.ProcessClassAfterUnpickling = Process

class ProcessInOtherProcess(Process):

    callAttempts = 3
    ## seconds to try to reestablish connection to the process
    minimumConnectionTrySeconds = 20

    debuglevel = 0

    def __init__(self, *args):
        Process.__init__(self, *args)
        self._connectionPossibilities = []
        self._connections = []
        self._lock = thread.allocate_lock()
        self._emptyCallQueueThread = None
        self._callQueue = None
        self._markedAsAlive = False
        self._triedToConnectOnce = False

    def debug(self, *args):
        if self.debuglevel >= 1:
            print '%s ' * len(args) % args

    def markAsDead(self):
        self._markedAsDead = True
        
    def markAsAlive(self):
        self._markedAsDead = False

    def isAlive(self):
        return not self._markedAsDead

    def addConnectionPossibility(self, possibility):
        self._connectionPossibilities.append(possibility)

    def hasConnection(self, aConnection):
        return aConnection in self._connections

    def hasConnections(self):
        return bool(self._connections)

    def addConnection(self, aConnection):
        import Process
        aConnection.fromProcess(Process.thisProcess)
        aConnection.toProcess(self)
        self._connections.append(aConnection)

    def _connect(self, connectionPossibility, notify):
        try:
            connection = connectionPossibility()
            if connection:
                self.debug('addConnection', connection)
                self.addConnection(connection)
        finally:
            notify()

    def newConnection(self):
        '''create a new connection'''
        connectionPossibilities = self._connectionPossibilities[:]
        if not connectionPossibilities:
            return 
        l = thread.allocate_lock()
        l2 = thread.allocate_lock()
        def notify():
            released = False
            for p in connectionPossibilities[1:]:
                self.debug('released:', released)
                if not released and self.hasConnections():
                    self.debug('release')
                    l.release()
                    released = True
                yield
            if not released: l.release()
            yield
        generator = notify()
        def notify():
            with l2:
                next(generator)
        l.acquire(False)
        for possibility in connectionPossibilities:
            thread.start_new(self._connect, (possibility, notify))
        l.acquire()
        self.debug('hasconnection!!!')

    @picklableAttribute
    def call(self, function, args, kw = {}):
        aConnection = self.chooseConnection()
        if aConnection is None:
            self.queueCall(function, args, kw)
            return 
        self.debug('connectionChosen')
        try:
            aConnection.call(function, args, kw)
            return
        except Listener.ConnectionBroken:
            self.queueCall(function, args, kw)
            self.removeConnection(aConnection)

    def queueCall(self, function, args, kw = {}):
        self.debug('QueueCall')
        if not self._emptyCallQueueThread: # speed up - no lock
            with self._lock:
                if not self._callQueue:
                    self._callQueue = queue = Queue.Queue()
                else: queue = self._callQueue
                if not self._emptyCallQueueThread:
                    self._emptyCallQueueThread = thread = threading.Thread(
                        target = self._emptyCallQueue,
                        args = (queue,))
                    thread.start()
        self._callQueue.put((function, args, kw))

    def _emptyCallQueue(self, queue):
        t = time.time()
        ttl = lambda: t + self.minimumConnectionTrySeconds - time.time()
        for i in range(self.callAttempts):
            call = queue.get(timeout = ttl())
            self.debug('create connection')
            if not self.hasConnections():
                self.newConnection()
            self.debug('call')
            self.call(*call)
            if  0 < ttl():
                break
        self.markAsDead()
    
    def removeConnection(self, aConnection):
        for i, ownConnection in reversed(list(enumerate(self._connections))):
            if ownConnection == aConnection:
                self._connections.pop(i)
                self.aConnectionRemoved(ownConnection)

    def aConnectionRemoved(self, aConnection):
        aConnection.close()
        
    def chooseConnection(self):
        'this raises'
        ## todo: better algorithm for aConnection attempts & choosing
        connections = self._connections[:1]
        if connections:
            return connections[0]
        with self._lock:
            ## To enable debug prints on connection failure and 
            ## to remove raise-conditions in testing
            if not self._triedToConnectOnce:
                self._triedToConnectOnce = True
                self.newConnection()
                return self.chooseConnection()
        return None

def addConnectionPossibilities(process, possibilities):
    for possibility in possibilities:
        process.addConnectionPossibility(possibility)
    return process

class _ThisProcess(Process):

    ProcessClassAfterUnpickling = ProcessInOtherProcess

    def __init__(self, _id):
        Process.__init__(self, _id, os.getpid(), socket.gethostname(),
                         time.time())
        self._listeners = []
        self._knownProcesses = set()
    
    @picklableAttribute
    def call(self, aFunction, args, kw = {}):
        return aFunction(*args, **kw)

    def addListener(self, aListener):
        if aListener not in self._listeners:
            self._listeners.append(aListener)
            self.addedListner(aListener)
        return aListener

    def addConnectionPossibility(self, possibility):
        pass

    def __reduce__(self):
        return addConnectionPossibilities, (R(Process.__reduce__(self)),
                                          self.getConnectionPossibilities())

    def getConnectionPossibilities(self):
        p = []
        for listener in self._listeners[:]:
            p.extend(listener.getConnectionPossibilities())
        return p

    def addedListner(self, aListener):
        aListener.listen()
        aListener.fromProcess(self)

    def removeListener(self, listener):
        'return the listeners removed.\n'\
        'They were equal to the one passed to this function'
        removedListeners = []
        for index, ownListener in reversed(list(enumerate(self._listeners[:]))):
            if ownListener == listener:
                self._listeners.pop(index)
                self.removedListener(ownListener)
                removedListeners.append(ownListener)
        return removedListeners
        
    def removedListener(self, listener):
        listener.close()

    def listenOnIPv4(self):
        if Listener.has_ipv4:
            return self.addListener(Listener.IPv4Listener())

    def listenOnPipe(self):
        if Listener.has_pipe:
            return self.addListener(Listener.PipeListener())

    def listenOnIPv6(self):
        if Listener.has_ipv6:
            return self.addListener(Listener.IPv6Listener())

    def listenOnUnix(self):
        if Listener.has_unix:
            return self.addListener(Listener.UnixListener())

    def listenWhereYouCan(self):
        ## order is important: put fastest first
        self.listenOnPipe()
        self.listenOnUnix()
        self.listenOnIPv6()
        self.listenOnIPv4()

    def acceptedConnection(self, aConnection):
        aConnection.fromProcess(self)
        setConnectionEndpoints(aConnection)

    def hasConnection(self, aConnection):
        return True

    def addConnection(self, aConnection):
        pass

    def knowsProcess(self, anotherProcess):
        self._knownProcesses.add(anotherProcess)

    @property
    def knownProcesses(self):
        return self._knownProcesses

    def stopListening(self):
        while self._listeners:
            listener = self._listeners.pop()
            listener.close()

    def __str__(self):
        return 'This' + Process.__str__(self)

IDENTITYLENGTH = 20

_id = os.urandom(IDENTITYLENGTH)
thisProcess = getProcess(_id, _ThisProcess, (_id,))
del _id

__all__ = ['getProcess', 'Process', 'thisProcess', 'ProcessCannotConnect'
           'ProcessInOtherProcess']
