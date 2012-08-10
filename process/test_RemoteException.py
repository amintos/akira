import traceback
import unittest
import StringIO
import sys

from RemoteException import *
from pickle import dumps, loads


class RemoteExceptionTest(unittest.TestCase):

    exceptionType = ValueError
    
    def f(self):
        raise self.exceptionType('this is exceptional!')

    def getError(self):
        try:
            self.f()
        except:
            return sys.exc_info()

    def assertIsRemoteError(self, error):
        self.assertIn(self.exceptionType.__name__, type(error).__name__)
        try:
            raise error
        except self.exceptionType:
            pass
        except:
            self.fail('error %s did not respond to original error class %s' % \
                      (error, self.exceptionType))
    
    def test_picklability(self):
        error = withTracebackPrint(*self.getError())
        self.assertIsRemoteError(error)
        for i in range(20):
            error = loads(dumps(error))
            self.assertIsRemoteError(error)

    def test_traceback_print_is_included(self):
        self.exceptionType = AssertionError
        error = self.getError()

        originalTraceback = StringIO.StringIO()
        traceback.print_exception(*error, file = originalTraceback)
        
        try:
            raise withTracebackPrint(*error)
        except self.exceptionType:
            finalTraceback = StringIO.StringIO()
            traceback.print_exc(file = finalTraceback)
##        print originalTraceback.getvalue()
##        print
##        print finalTraceback.getvalue()
        self.assertIn(originalTraceback.getvalue(), finalTraceback.getvalue())

    def test_can_pickle_exc_info_type(self):
        error = self.getError()
        try:
            raise withTracebackPrint(*error)
        except self.exceptionType:
            ty, err, tb = sys.exc_info()
            
        ty2 = loads(dumps(ty))
        self.assertEquals(ty2, ty)

    def test_arguments_remain(self):
        error = self.getError()
        originalArgs = error[1].args
        remoteArgs = withTracebackPrint(*error).args
        self.assertEquals(remoteArgs, originalArgs)

    def test_catch_remote_exception(self):
        try:
            raise asRemoteException(ReferenceError)(ReferenceError(),'')
        except asRemoteException(ReferenceError):
            pass
        

if __name__ == '__main__':
    unittest.main(exit = False)
