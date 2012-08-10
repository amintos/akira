import traceback
import StringIO
from copy_reg import dispatch_table, pickle

def withTracebackPrint(ErrorType, thrownError, _traceback):
    file = StringIO.StringIO()
    file.write('\n')
    traceback.print_exception(ErrorType, thrownError, _traceback, file = file)
    return _loadError(ErrorType, thrownError, file.getvalue())
    ## why don't we just use the following line?
    ## return ErrorType(file.getvalue())
    ## because the arguments would get hurt
    ## or the traceback print has no unescaped newlines

class _RemoteExceptionMeta(type):
    pass
                    
def _pickle_function(RemoteExceptionClass):
    return _loadErrorType, (RemoteExceptionClass.BaseExceptionType,)

pickle(_RemoteExceptionMeta, _pickle_function)

_remoteExceptionCache = {} # exception : RemoteException

def _newRemoteException(ErrorType):
    RemoteErrorBaseType = _RemoteExceptionMeta('', (ErrorType,), {})
    class RemoteException(RemoteErrorBaseType):
        BaseExceptionType = ErrorType
        
        def __init__(self, thrownError, tracebackString):
            self.thrownError = thrownError
            self.tracebackString = tracebackString
            RemoteErrorBaseType.__init__(self, *thrownError.args)
            
        loadError = staticmethod(_loadError)
        
        def __str__(self):
            return '\n%s\n%s' % (self.tracebackString, self.thrownError)

        def __reduce__(self):
            args = (ErrorType, self.thrownError, self.tracebackString)
            return self.loadError, args
    RemoteException.__name__ = 'Remote' + ErrorType.__name__
    return RemoteException


def _loadErrorType(ErrorType):
    RemoteException = _remoteExceptionCache.get(ErrorType)
    if RemoteException is None:
        RemoteException = _newRemoteException(ErrorType)
        _remoteExceptionCache.setdefault(ErrorType, RemoteException)
        return _remoteExceptionCache.get(ErrorType)
    return RemoteException

def _loadError(ErrorType, thrownError, tracebackString):
    RemoteException = _loadErrorType(ErrorType)
    return RemoteException(thrownError, tracebackString)
    
    
__all__ = ['withTracebackPrint']
