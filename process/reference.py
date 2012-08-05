import sys

from LocalObjectDatabase import LocalObjectDatabase

from proxy import ProxyWithExceptions, insideProxy, outsideProxy
from multiprocessing.pool import ApplyResult

class Objectbase(LocalObjectDatabase):
    pass
assert Objectbase() is objectbase

## optimize: use weak db in some cases

class Reference(ProxyWithExceptions):
    exceptions = ('__reduce__', '__reduce_ex__')

    @insideProxy
    def __init__(self, reference, method):
        self.call = method
        self.reference = reference
        self.initArguments = reference, method

##    @insideProxy
##    def call(self, methodName, args, kw):
##        return self.method(self.reference, methodName, args, kw)

    @insideProxy
    def __reduce__(self):
        return self.__class__, self.initArguments

    @classmethod
    def isReference(cls, obj):
        return issubclass(type(obj), cls)

#
# proxy methods for asynchronous send only
#

def _send_execute(reference, methodName, args, kw):
    assert reference.isLocal()
    method = getattr(reference.value, methodName)
    return method(*args, **kw)

def send(reference, methodName, args, kw):
    reference.process.call(_send_execute, (reference, methodName, args, kw))

#
# proxy methods for asynchronous send and receive 
#

class Result(ApplyResult):

    def setValue(self, value):
        self._set(None, (True, value))

    def setError(self, ty, err, tb):
        self.error = (ty, err, tb)
        self._set(None, (False, err))

def _async_execute(resultReference, reference, methodName, args, kw):
    try:
        result = _send_execute(reference, methodName, args, kw)
        send(resultReference, 'setValue', (result,), {})
    except:
        ty, err, tb = sys.exc_info()
        ## todo: include traceback
        send(resultReference, 'setError', (ty, err, None), {})
    

def async(reference, methodName, args, kw, callback = None):
    result = ApplyResult({}, callback)
    resultReference = objectbase.store(result)
    args = (resultReference, reference, methodName, args, kw)
    reference.process.call(_async_execute, args)
    return result

#
# proxy methods for synchronous send and receive
#

def sunc(*args):
    result = async(*args)
    return result.get()

#
# proxy methods for callback communication
#

def callback(reference, methodName, args, kw):
    assert args, 'the callback must be the first argument'
    assert callable(args[0]), 'the callback must be the first argument'
    callback = args[0]
    methodArgs = args[1:]
    return async(reference, methodName, methodArgs, kw, callback = callback)
    
