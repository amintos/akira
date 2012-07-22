import socket
import time
import thread
import os




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
        return getProcess, (self.identityString, self.ProcessClassAfterUnpickling,
                            (self.identityString, self.pid,
                             self.hostName, self.creationTime),)

    def __eq__(self, other):
        return self.identityString == other.identityString

    def __hash__(self):
        return hash(self.identityString)

    def __le__(self, other):
        return self.creationTime < other.creationTime

    def isThisProcess(self):
        return thisProcess is self

    def isProcess(self):
        return True

Process.ProcessClassAfterUnpickling = Process

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


class _ThisProcess(Process):

    def __init__(self, *args, **kw):
        Process.__init__(self, *args, **kw)
        self._listeners = []
    
    def call(self, aFunction, args, kw = {}):
        return aFunction(*args, **kw)

    def addListener(self, aListener):
        if aListener not in self._listeners:
            self._listeners.append(aListener)
            self.addedListner(aListener)

    def addedListner(self, aListener):
        aListener.listen()

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
thisProcess = getProcess(_id, _ThisProcess, (_id, os.getpid(),
                                             socket.gethostname(), time.time()))
del _id

__all__ = ['getProcess', 'Process', 'thisProcess', 'IDENTITYLENGTH']
