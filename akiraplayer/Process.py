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
        self._listeners = []

        for listener in listeners:
            self.addListener(listener)

    @property
    def identityString(self):
        return self._identityString

    def addListener(self, aListener):
        if aListener not in self._listeners:
            self._listeners.append(aListener)
            self.addedListner(aListener)

    def addedListner(self, aListener):
        pass

    def call(self, aFunction, args, kw):
        raise NotImplementedError('todo')    
    
    def __reduce__(self):
        return getProcess, (identityString, Process, (identityString, pid,
                                                      hostName, creationTime),)

    def __eq__(self, other):
        return self.identityString == other.identityString

    def __hash__(self):
        return hash(self.identityString)

    def __le__(self, other):
        return self.creationTime < other.creationTime

    def isThisProcess(self):
        return thisProcess is self


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
    def call(self, aFunction, args, kw):
        return aFunction(*args, **kw)

    def addedListner(self, aListener):
        aListener.listen()

IDENTITYLENGTH = 20

_id = os.urandom(IDENTITYLENGTH)
thisProcess = getProcess(_id, _ThisProcess, (_id, os.getpid(),
                                             socket.gethostname(), time.time()))
del _id

__all__ = ['getProcess', 'Process', 'thisProcess', 'IDENTITYLENGTH']
