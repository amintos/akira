
import traceback
import itertools
import thread
import Process

from VeryPicklableObject import picklable, picklableAttribute

class DatabaseReference(object):
    def __init__(self, database, process, _id, *args, **kw):
        assert _id is not None
        self.database = database
        self.process = process
        self.id = _id
        self.init(*args, **kw)
##        print 'new %s' % self

    def init(self, *args, **kw):
        raise NotImplementedError('to be implemented in subclasses')

    def isLocal(self):
        return False

    def isDirect(self):
        return False

    def isIndirect(self):
        return False

    def localProcess(self):
        return self.database.localProcess()

    def __str__(self):
        return '%s(%s->%s->%s)' % (self.__class__.__name__, self.database, self.process, self.id)

    def _delete(self):
        pass

    def __del__(self):
        self._delete()


class LocalDatabaseReference(DatabaseReference):

    def init(self, reference = None):
##        print self
        pass
    
    def isLocal(self):
        return self.process.isThisProcess()

    @property
    def value(self):
        return self.database.loadObjectById(self.id)

    @value.setter
    def value(self, newValue):
        self.database.storeObjectToId(newValue, self.id)
    
    def duplicateId(self):
        return self.database.duplicateObjectById(self.id)

    def __reduce__(self):
        args = (self.process, self.duplicateId())
##        print '__reduce__', self, args
        return self.database.loadFromLocalReference, args

    def _delete(self):
        self.database.freeObjectById(self.id)

class RemoteDatabaseReference(DatabaseReference):

    def isDirect(self):
        return True

    def init(self):
        pass

    def storedLocally(self):
        ref = self.database.newLocalReference()
        ref.value = self
        return ref
    
    def __reduce__(self):
        args = self.process, self.id, self.storedLocally()
        return self.database.loadFromRemoteReference, args

    def _delete(self):
        self.process.call(self.database.freeObjectById, (self.id,))
    
def sendNewId(fromProcess, localReference, toProcess, ref2ref):
    assert localReference.isLocal()
##    print 'sendNewId', fromProcess, localReference, toProcess, ref2ref
    toProcess.call(receiveNewId, (fromProcess, localReference, ref2ref))

def receiveNewId(fromProcess, newRef, ref2ref):
    ## todo: if error here: free reference in fromProcess
    ref = ref2ref.value
    ref.getIdFromReference(newRef)

class IndirectRemoteDatabaseReference(RemoteDatabaseReference):

    def isIndirect(self):
        return not self.isDirect()

    def isDirect(self):
        return self.receivedNewReference

    def init(self, reference):
        self.reference = reference
        self.receivedNewReference = False
        self.getNewId()


    def getNewId(self):
        assert self.reference is not None
        localSelf = self.database.store(self)
        self.process.call(sendNewId, (self.process, self, \
                                      self.localProcess(), localSelf))

    def storedLocally(self):
        ref = self.database.newLocalReference()
        if self.reference is None:
            print 'ahsdfladsjhfjkasdfk'
            ref.value = self
        else:
            ref.value = self.reference
        return ref

    def getIdFromReference(self, reference):
        assert self.process == reference.process
        self.id = reference.id
        self.reference = reference
        self.receivedNewReference = True

    def _delete(self):
        assert self.receivedNewReference, 'there should be a callback'\
               ' referencing me while I wait for the callback'
        del self.reference


class LocalObjectDatabase(object):

    LocalDatabaseReference = LocalDatabaseReference
    RemoteDatabaseReference = RemoteDatabaseReference
    IndirectRemoteDatabaseReference = IndirectRemoteDatabaseReference

    @picklable
    class ObjectNotFound(Exception):
        '''The object could not be found in the database'''
        pass

    def __init__(self):
        self.__id_lock = thread.allocate_lock()
        self.__id_counter = itertools.count()
        self.objectStore = {} # id: obj
        self.storeUnderName()
        
    def getId(self):
        with self.__id_lock:
            return next(self.__id_counter)

    def storeObjectToId(self, obj, _id):
        assert type(_id) is int or type(_id) is long
##        print 'store', self, obj, _id
        self.objectStore[_id] = obj

    def loadObjectById(self, _id):
        l = []
        obj = self.objectStore.get(_id, l)
        if obj is l:
            raise self.ObjectNotFound('the object with id %r was deleted' % _id)
        return obj

    def hasObjectById(self, _id):
        l = []
        obj = self.objectStore.get(_id, l)
        return obj is not l

    @picklableAttribute
    def freeObjectById(self, _id):
        l = []
        if self.objectStore.pop(_id, l) is l:
            raise self.ObjectNotFound('the object with id %r was deleted' % _id)

    def duplicateObjectById(self, _id):
        newId = self.getId()
        obj = self.loadObjectById(_id)
        self.storeObjectToId(obj, newId)
##        print 'duplicateObjectById %s %s->%s' % (self, _id, newId)
        return newId

    def storeUnderName(self):
        module = self.getModule()
        name = self.getName()
        assert not hasattr(module, name), \
               'there can only be one database under this name'
        setattr(module, name, self)

    def getName(self):
        name = self.__class__.__name__
        return name[0].lower() + name[1:]

    @classmethod
    def getModule(cls):
        module = __import__(cls.__module__)
        assert getattr(module, cls.__name__) is cls
        return module

    def __reduce__(self):
        return self.getName()

    def localProcess(self):
        return Process.thisProcess

    def newLocalReference(self):
        return self.LocalDatabaseReference(self, self.localProcess(), \
                                           self.getId())
    
    def _getLocalDatabaseReference(self, process, _id, *args):
##        print '_getLocalDatabaseReference', process, process.isThisProcess(), _id
        newId = self.duplicateObjectById(_id)
        return self.LocalDatabaseReference(self, process, newId, *args)
    
    @picklable
    def loadFromLocalReference(self, process, *args):
        if process.isThisProcess():
            return self._getLocalDatabaseReference(process, *args)
        return self.RemoteDatabaseReference(self, process, *args)

    @picklable
    def loadFromRemoteReference(self, process, *args):
        if process.isThisProcess():
            return self._getLocalDatabaseReference(process, *args)
        return self.IndirectRemoteDatabaseReference(self, process, *args)

    def store(self, obj):
        ref = self.newLocalReference()
        ref.value = obj
        return ref

    def delete(self):
        module = self.getModule()
        name = self.getName()
        if self is getattr(module, name):
            delattr(module, name)
        
    def __str__(self):
        return '%s.%s' % (self.getModule().__name__, self.getName())
