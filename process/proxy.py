import sys
import magicMethods

from SelfWrap import objectGetattributeFunction as insideProxy
from SelfWrap import getObject as outsideProxy


_cached_classes = {} # object type : constructed

def shortenTraceback():
    ## copy this code to where you need it
    ty, err, tb = sys.exc_info()
    if tb.tb_next is not None:
        tb = tb.tb_next ## shorten traceback
    raise ty, err, tb

class Proxy(object):
    '''Proxy(object)

this proxy puts all method calls through to the object

    object.a
    object.a = 1
    object.a()

'''

    noMagicMethodNames = set(['__init__'])
    ## todo: remove inplace methods
    
    @classmethod
    def updateMagicMethods(cls, magicMethodNames):
        cls.createMagicMethods(magicMethodNames - cls.noMagicMethodNames)

    @classmethod
    def afterClassCreation(cls):
        # todo: call this after class is created
        cls.updateMagicMethods(magicMethods.magicMethods)
        magicMethods.onChange(cls.updateMagicMethods)

    @classmethod
    def createMagicMethod(cls, methodName):
        @insideProxy
        def magicMethod(self, *args, **kw):
            try:
                return self.call(methodName, args, kw)
            except:
                ty, err, tb = sys.exc_info()
                if tb.tb_next is not None:
                    tb = tb.tb_next ## shorten traceback
                raise ty, err, tb
        magicMethod.__name__ = methodName
        setattr(cls, methodName, magicMethod)

    @classmethod
    def createMagicMethods(cls, magicMethodsNames):
        for methodName in magicMethodsNames:
            cls.createMagicMethod(methodName)

    @insideProxy
    def __init__(self, enclosedObject):
        self.enclosedObject = enclosedObject

    @insideProxy
    def call(self, methodName, args, kw):
        try:
            return getattr(self.enclosedObject, methodName)(*args, **kw)
        except:
            ty, err, tb = sys.exc_info()
            if tb.tb_next is not None:
                tb = tb.tb_next ## shorten traceback
            raise ty, err, tb

Proxy.afterClassCreation()

def proxy(obj):
    return Proxy(obj)

class ProxyWithExceptions(Proxy):
    exceptions = ()

    @insideProxy
    def __getattribute__(self, name):
        try:
            if name in self.exceptions:
                return getattr(self, name)
            return Proxy.__getattribute__(self, name)
        except:
            ty, err, tb = sys.exc_info()
            if tb.tb_next is not None:
                tb = tb.tb_next ## shorten traceback
            raise ty, err, tb


def isProxy(obj):
    return issubclass(type(obj), Proxy)
