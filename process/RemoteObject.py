import itertools
import thread
import Process
from proxy import ProxyWithExceptions, insideProxy, isProxy, outsideProxy
from R import R

class ObjectNotFound(Exception):
    '''The object could not be found in the database'''
    pass

_id_lock = thread.allocate_lock()
_id_counter = itertools.count()
def getId():
    with _id_lock:
        return next(_id_counter)

proxyObjectDatabase = {} # id: obj

def storeObject(obj):
    _id = getId()
    proxyObjectDatabase[_id] = obj
    return _id

def loadObject(_id):
    l = []
    obj = proxyObjectDatabase.get(_id, l)
    if obj is l:
        raise ObjectNotFound('the object with id %r was deleted' % _id)
    return obj

def freeObject(_id):
    l = []
    if proxyObjectDatabase.pop(_id, l) is l:
        raise ObjectNotFound('the object with id %r was deleted' % _id)

def loadDirectReferenceOrObject(process, _id):
    if process == Process.thisProcess:
        return onlyInThisProcess(loadObject(_id))
    return DirectRemoteReference(process, _id)

def loadIndirectReferenceOrObject(process, _id, proxy):
    if process == Process.thisProcess:
        return onlyInThisProcess(loadObject(_id))
    return IndirectRemoteReference(process, _id, proxy)

class LocalObject(ProxyWithExceptions):
    exceptions = ('__reduce__','__reduce_ex__')

    @insideProxy
    def __init__(self, enclosedObject, process = Process.thisProcess):
        ProxyWithExceptions.__init__(self, enclosedObject)
        self.process = process

    @insideProxy
    def __reduce__(self):
        _id = storeObject(self.enclosedObject)
        return loadDirectReferenceOrObject, (self.process, _id)

    def __reduce_ex__(self, proto):
        return self.__reduce__()

def callAttr(objId, attr, args, kw):
    return apply(getattr(loadObject(objId), attr), args, kw)

class DirectRemoteReference(ProxyWithExceptions):
    exceptions = ('__reduce__','__reduce_ex__')

    @insideProxy
    def __init__(self, process, _id):
        ProxyWithExceptions.__init__(self, None)
        self.process = process
        self.id = _id
        self.acquireNewId()

    @insideProxy
    def acquireNewId(self):
        pass

    @insideProxy
    def __reduce__(self):
        selfref = LocalObject(outsideProxy(self), self.process)
        return loadIndirectReferenceOrObject, (self.process, self.id, \
                                               selfref)

    @insideProxy
    def __reduce_ex__(self, proto):
        return self.__reduce__()

    @insideProxy
    def __del__(self):
        print '__del__'
        self.process.call(freeObject, (self.id,))

    @insideProxy
    def call(self, functionName, args, kw):
        return self.process.call(callAttr, (self.id, functionName, args, kw))

def assignNewId(_id, callback):
    callback(storeObject(loadObject(_id)))

class IndirectRemoteReference(DirectRemoteReference):

    @insideProxy
    def __init__(self, process, _id, proxy):
        self.proxy = proxy
        DirectRemoteReference.__init__(self, process, _id)

    @insideProxy
    def acquireNewId(self):
        self.process.call(assignNewId,
                          (self.id, onlyInThisProcess(self.setId)))

    @insideProxy
    def setId(self, newId):
        print 'setId', self.id, newId
        self.id = newId
        del self.proxy
        

def onlyInThisProcess(obj):
    remoteObject = LocalObject(obj)
    if isProxy(obj):
        return remoteObject
    try:
        obj.__reduce__ = remoteObject.__reduce__
        obj.__reduce_ex__ = remoteObject.__reduce_ex__
    except AttributeError:
        return remoteObject
    else:
        if obj.__reduce__ != remoteObject.__reduce__ or \
           obj.__reduce_ex__ != remoteObject.__reduce_ex__:
            return remoteObject
        return obj

__all__ = ['onlyInThisProcess']
