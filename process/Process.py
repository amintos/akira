import socket
import time
import thread
import os
from R import R

from VeryPicklableObject import picklableAttribute
import Listener
from setConnectionEndpointsAlgorithm import setConnectionEndpoints

_cachedProcesses = {}
_cachedProcessesLock = thread.allocate_lock()

class ProcessCannotConnect(Listener.ConnectionBroken):
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

    def isThisProcess(self):
        return thisProcess is self

    def isProcess(self):
        return True

    def __str__(self):
        return 'Process %s on %s' % (self.pid, self.hostName)

Process.ProcessClassAfterUnpickling = Process

class ProcessInOtherProcess(Process):

    callAttempts = 10

    def __init__(self, *args):
        Process.__init__(self, *args)
        self._connectionPossibilities = []
        self._connections = []

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

    def newConnection(self):
        for possibility in self._connectionPossibilities:
            aConnection = possibility()
            if aConnection is not None:
                self.addConnection(aConnection)
                return aConnection
        return None

    @picklableAttribute
    def call(self, function, args, kw = {}):
        for i in xrange(self.callAttempts):
            aConnection = self.chooseConnection()
            try:
                aConnection.call(function, args, kw)
                return
            except Listener.ConnectionBroken:
                self.removeConnection(aConnection)
        raise ProcessCannotConnect('tried to connect %i times but failed' % \
                                   self.callAttempts)

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
        if not self.hasConnections():
            aConnection = self.newConnection()
        else:
            aConnection = self._connections[0]
        if aConnection is None:
            raise ProcessCannotConnect('all connection possibilities failed')
        return aConnection

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
