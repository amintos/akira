"""
helper for ordinary access to classinstances after having overwritten __getattribute__
this does not work for type instances

"""

import sys

def aspectSelfWrap(BaseClass):
    __setattr__= BaseClass.__setattr__
    __getattribute__= BaseClass.__getattribute__
    __delattr__= BaseClass.__delattr__
    
    class SelfWrap(BaseClass):
                
        def __init__(self, obj):
            __setattr__(self, 'obj', obj)

        def __setattr__(self, name, value):
            return __setattr__(__getattribute__(self, 'obj'), name, value)

        def __getattribute__(self, name):
            return __getattribute__(__getattribute__(self, 'obj'), name)

        def __delattr__(self, name):
            return __delattr__(__getattribute__(self, 'obj'), name)
            
    return SelfWrap

SelfWrap= aspectSelfWrap(object)

def objectGetattributeFunction(function):
    ''' use __getattribute__, __setattr__, __delattr__ of object
@objectGetattributeFunction
def function(self, ...):
    'self uses __getattribute__, __setattr__, __delattr__ of object'
    ...

# same as
@use_getattribute(object)
def function(self, ...):
    ...

'''
    def objectGetattributeFunctionReplacement(self, *args, **kw):
        try:
            return function(SelfWrap(self), *args, **kw)
        except:
            # skip this traceback
            ty, er, tb= sys.exc_info()
            if tb.tb_next:
                tb= tb.tb_next
            raise ty, er, tb
    return objectGetattributeFunctionReplacement
            
def use_getattribute(BaseClass):
    ''' use __getattribute__, __setattr__, __delattr__ of BaseClass
@use_getattribute(BaseClass)
def function(self, ...):
    'self uses __getattribute__, __setattr__, __delattr__ of BaseClass'
    ...
    
'''
    _SelfWrap= aspectSelfWrap(BaseClass)
    def function(function):
        def objectGetattributeFunctionReplacement(self, *args, **kw):
            try:
                #print 'objectGetattributeFunctionReplacement:', self, args, kw, function
                #print '_SelfWrap:', _SelfWrap
                return function(_SelfWrap(self), *args, **kw)
            except:
                # scip this traceback
                ty, er, tb= sys.exc_info()
                if tb.tb_next:
                    tb= tb.tb_next
                raise ty, er, tb
        return objectGetattributeFunctionReplacement
    return function
