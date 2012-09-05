import sys

from LocalObjectDatabase import LocalObjectDatabase

from proxy import Proxy, insideProxy, outsideProxy
from multiprocessing.pool import ApplyResult
import RemoteException

class Objectbase(LocalObjectDatabase):
    pass
assert Objectbase() is objectbase

## optimize: use weak db in some cases

class AttributeReference(object):
    def __init__(self, reference, attribute):
        self.reference = reference
        self.attribute = attribute
        self.takeOverAttributes()

    def takeOverAttributes(self):
        self.process = self.reference.process
        self.isLocal = self.reference.isLocal

    @property
    def value(self):
        return getattr(self.reference.value, self.attribute)

    def __repr__(self):
        return repr(self.reference) + '.' + str(self.attribute)

    def __reduce__(self):
        return AttributeReference, (self.reference, self.attribute)


class ReferenceProxy(Proxy):
    '''this '''
    exclusions = ('__reduce__', '__reduce_ex__')

    TIMEOUT_FOR_SPECIAL_FUNCTIONS = 5 # seconds

    @insideProxy
    def __init__(self, method, reference):
        self.method = method
        self.reference = reference
        self.initArguments = method, reference

    @insideProxy
    def call(self, methodName, args, kw):
        try:
            return self.method(self.reference, methodName, args, kw)
        except:
            ty, err, tb = exc_info_without_reference()
            raise ty, err, tb

    @insideProxy
    def getReference(self):
        return self.reference

    @insideProxy
    def __reduce__(self):
        return self.__class__, self.initArguments

    def __reduce_ex__(self, proto):
        return self.__reduce__()

    @classmethod
    def isReferenceProxy(cls, obj):
        return issubclass(type(obj), cls)

    @insideProxy
    def __getattribute__(self, name):
        if name in self.exclusions:
            return getattr(self, name)
        return self.bindMethod(name)

    @insideProxy
    def bindMethod(self, name):
        reference = AttributeReference(self.reference, name)
        return self.newReference(self.method, reference)

    @insideProxy
    def getMethod(self):
        return self.method

    @classmethod
    def newReference(cls, *args):
        return cls(*args)

#
# proxy methods for asynchronous send only
#

def _send_execute(reference, methodName, args, kw):
    assert reference.isLocal()
    method = getattr(reference.value, methodName)
    return method(*args, **kw)

def send(reference, methodName, args, kw):
    '''only send the calls to the object.
Nothing is returned, No Errors handled.'''
    reference.process.call(_send_execute, (reference, methodName, args, kw))


#
# asynchronous traceback transfer options
#

def exc_info_without_reference(exc_info = sys.exc_info):
    ty, err, tb = exc_info()
    # skip three reference internal calls
    _globals = globals()
    while tb and tb.tb_frame.f_globals is _globals:
        tb = tb.tb_next
    return ty, err, tb

def exc_info_no_traceback(exc_info = sys.exc_info):
    '''just transfer the error and the type
the traceback is dropped'''
    ty, err, tb = exc_info()
    return ty, err, None

def exc_info_print_traceback(exc_info = exc_info_without_reference):
    '''transfer a RemoteException of the error
the traceback is printed along with the original error'''
    ty, err, tb = exc_info()
    error = RemoteException.withTracebackPrint(ty, err, tb)
    return None, error, None

## todo: add here traceback references


#
# proxy methods for asynchronous send and receive 
#

class Result(ApplyResult):

    def __init__(self, callback = None):
        ApplyResult.__init__(self, {}, callback)
        
    def setValue(self, value):
        self._set(None, (True, value))

    def setError(self, ty, err, tb):
        self.error = (ty, err, tb)
        self._set(None, (False, err))

    def getError(self):
        return self.error

def _async_execute(resultReference, reference, methodName, args, kw, \
                   exc_info = exc_info_print_traceback):
    '''execute the asynchronous call in the local process'''
    try:
        result = _send_execute(reference, methodName, args, kw)
        send(resultReference, 'setValue', (result,), {})
    except:
        send(resultReference, 'setError', exc_info(), {})

def async(reference, methodName, args, kw, callback = None, **kwargs):
    '''call the methods of the object.
returns a Result object.

optional arguments:
    exc_info
        should be a function that is called instead of sys.get_exc():
	exc_info_no_traceback
	exc_info_print_traceback
    callback
        a function that is called with every result returned
        callback(aValue)
	
'''
    result = Result(callback)
    resultReference = objectbase.store(result)
    args = (resultReference, reference, methodName, args, kw)
##    print args
    reference.process.call(_async_execute, args, kwargs)
    return result

#
# proxy methods for synchronous send and receive
#

def sync(*args, **kw):
    '''synchonously call the methods of the object.
This is the typical communication of python.
It can make the program slow.

optional arguments:
    timeout
        None or the time in seconds to wait for a result of a call
    see async for more arguments
'''
    timeout = kw.pop('timeout', None)
    result = async(*args, **kw)
    return result.get(timeout)

#
# proxy methods for callback communication
#

def callback(reference, methodName, args, kw, **kwargs):
    '''call the methods of the object but pass a callback as first argument
this callback receives the result.get() if no error occurred'''
    assert args, 'the callback must be the first argument'
    assert callable(args[0]), 'the callback must be the first argument'
    callback = args[0]
    methodArgs = args[1:]
    return async(reference, methodName, methodArgs, kw, callback = callback,
                 **kwargs)


#
# creating references
#

def reference(obj, method, ProxyClass = ReferenceProxy):
    '''reference an object and adapt communication to the method
the object can also be a Reference. So the method can be changed'''
    if ProxyClass.isReferenceProxy(obj):
        reference = ProxyClass.getReference(obj)
    else:
        reference = objectbase.store(obj)
    return ProxyClass(method, reference)

def referenceMethod(reference, ProxyClass = ReferenceProxy):
    '''get the method of referencing the object from a object
that was returned by reference()'''
    assert ProxyClass.isReferenceProxy(reference)
    return ProxyClass.getMethod(reference)
        
__all__ = ['reference', 'callback', 'sync', 'async', 'send', 'ReferenceProxy', \
           'referenceMethod', 'AttributeReference']
