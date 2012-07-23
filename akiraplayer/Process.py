import socket
import time
import thread
import os

_cachedProcesses = {}
_cachedProcessesLock = thread.allocate_lock()

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
        self._identityString = identityString
        self.pid = pid
        self.hostName = hostName
        self.creationTime = creationTime

    @property
    def identityString(self):
        return self._identityString

    def call(self, aFunction, args, kw = {}):
        raise NotImplementedError('todo')    
    
    def __reduce__(self):
        return self.getLoadFunction(), \
                (self.identityString, self.ProcessClassAfterUnpickling,
                 (self.identityString, self.pid, self.hostName,
                  self.creationTime),)

    def getLoadFunction(self):
        '=> function to use to load process after transfer over connections'
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

class R(object):
    def __init__(self, reducedRepresentation):
        self.reducedRepresentation = reducedRepresentation
    def __reduce__(self):
        return self.reducedRepresentation
    def __call__(self):
        raise NotImplementedError('this should never be called')

class ProcessInOtherProcess(Process):

    def __init__(self, *args):
        Process.__init__(self, *args)
        self._connectionPossibilities = []
        self._connections = []

    def addConnectionPossibility(self, possibility):
        self._connectionPossibilities.append(possibility)

    def addConnection(self, aConnection):
        import Process
        aConnection.fromProcess(Process.thisProcess)
        aConnection.toProcess(self)
        self._connections.append(aConnection)

    def newConnection(self):
        for possibility in self._connectionPossibilities:
            connection = possibility()
            if connection is not None:
                self.addConnection(connection)
                return connection
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
    
    def call(self, aFunction, args, kw = {}):
        return aFunction(*args, **kw)

    def addListener(self, aListener):
        if aListener not in self._listeners:
            self._listeners.append(aListener)
            self.addedListner(aListener)

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
        raise NotImplementedError('todo')

    def listenOnPipe(self):
        raise NotImplementedError('todo')

    def listenOnIPv6(self):
        raise NotImplementedError('todo')

    def listenOnUnix(self):
        raise NotImplementedError('todo')



IDENTITYLENGTH = 20

_id = os.urandom(IDENTITYLENGTH)
thisProcess = getProcess(_id, _ThisProcess, (_id,))
del _id

__all__ = ['getProcess', 'Process', 'thisProcess', 'IDENTITYLENGTH',
           'ProcessInOtherProcess']
