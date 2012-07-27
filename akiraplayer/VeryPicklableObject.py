from proxy import ProxyWithExceptions, insideProxy, outsideProxy
from R import R

class X(object):
    def m(self):pass
    @staticmethod
    def m_static():pass
    @classmethod
    def m_class(cls):pass

def f():pass

class CannotWrapThisObject(Exception):
    pass

returnUnwrappedObject = lambda obj, self: obj

class Picklable(object):

    def __init__(self):
        self.replaceTypes = {}

    def wrap(self, obj, type, default = None):
        replacement = self.replaceTypes.get(type, default)
        if replacement is None:
            raise CannotWrapThisObject(
                            'No replacement found for %r of type %r. '\
                            'If you have one use %s.addReplacement' % \
                            (obj, type, self.__class__.__name__))
        return replacement(obj, self)

    def addReplacement(self, objectType, replacementFunction):
        self.replaceTypes[objectType] = replacementFunction

    def replacement(self, replacement):
        self.addReplacement(replacement.getType(), replacement.getReplacement())
        self.addReplacement(replacement, returnUnwrappedObject)
        return replacement

    def __reduce__(self):
        ## other subclasses will need to overwrite this
        return 'picklable'
        
    def __call__(self, obj):
        'wrap an object so it can be pickled'
        return self.wrap(obj, type(obj))

    def wrapWithDefault(self, obj, default):
        return self.wrap(obj, type(obj), returnUnwrappedObject)

picklable = Picklable()

class PicklableType(object):
    picklable = picklable
    def __init__(self, type):
        self.__module__ = __name__
        self.type = type
        self.__name__ = '_TYPE_' + type.__module__ + '.' + type.__name__
        globals()[self.__name__] = self
    def __reduce__(self):
        return self.__name__
    def __call__(self, *args, **kw):
        return self.picklable(self.type(*args, **kw))

class picklableBase(ProxyWithExceptions):

    exceptions = ['__reduce__', '__reduce_ex__', '__class__']
    n = None

    @insideProxy
    def __init__(self, enclosedObject, picklable):
        ProxyWithExceptions.__init__(self, enclosedObject)
        self.picklable = picklable
        self.prepareObject(enclosedObject)

    def prepareObject(self, enclosedObject):
        'overwrite this instead if __init__'
        pass

    @classmethod
    def createWrapMethod(cls, methodName):
        @insideProxy
        def wrapMethod(self, *args, **kw):
            obj = self.call(methodName, args, kw)
            return self.picklable.wrapWithDefault(obj, obj)
        wrapMethod.__name__ = methodName
        setattr(cls, methodName, wrapMethod)
    
    def __reduce__(self):
        raise NotImplementedError('to be implemented in subclasses.')

    def __reduce_ex__(self, proto):
        return self.__reduce__()

    @classmethod
    def getType(cls):
        if not cls.n:
            raise ValueError('n is not set')
        return cls.n.type

    @property
    @insideProxy
    def obj(self):
        return self.enclosedObject

    @classmethod
    def getReplacement(cls):
        return cls

    @insideProxy
    def __eq__(self, other):
        if issubclass(type(other), picklableBase):
            return other == self.enclosedObject
        return self.enclosedObject == other

    def __ne__(self, other):
        return not self == other

class pickleableWithGetter(picklableBase):
    pass

pickleableWithGetter.createWrapMethod('__get__')

@picklable.replacement
class picklableInstancemethod(pickleableWithGetter):

    n = PicklableType(type(X.m))

    @insideProxy
    def prepareObject(self, im):
        self.function = self.picklable(im.im_func)

    @insideProxy
    def __reduce__(self):
        return self.n, (self.function, self.obj.im_self, self.obj.im_class)

def getName(function):
    return 'PICKLABLE.' + type(function).__name__ + '.' + function.__name__


class _picklableFunction(pickleableWithGetter):

    n = PicklableType(type(f))

    @insideProxy
    def prepareObject(self, function):
        self.__module__ = function.__module__
        self.__name__ = getName(function)
        outside = outsideProxy(self)
        if self.__name__ in function.func_globals and \
            not outside == function.func_globals[self.__name__]:
            raise NameError('cannot mock a function that already exists in the module')
        function.func_globals[self.__name__] = outside

    @insideProxy
    def __reduce__(self):
        return self.__name__

def picklableFunction(function, picklable):
    'make globally stored function objects unique for pickle'
    name = getName(function)
    if name in function.func_globals:
        obj = function.func_globals[name]
        if type(obj) is _picklableFunction:
            return obj
    return _picklableFunction(function, picklable)

picklable.addReplacement(type(f), picklableFunction)
picklable.addReplacement(_picklableFunction, returnUnwrappedObject)
    


@picklable.replacement
class picklableClassmethod(pickleableWithGetter):

    n = PicklableType(classmethod)

    @insideProxy
    def prepareObject(self, classMethod):
        self.function = self.picklable(classMethod.__func__)

    @insideProxy
    def __eq__(self, other):
        return self.function == other

    @insideProxy
    def __reduce__(self):
        return self.n, (self.function, )

@picklable.replacement
class picklableStaticmethod(picklableClassmethod):
    
    n = PicklableType(staticmethod)
##    
##class picklableAttribute(object):
##
##    def __init__(self, function):
##        self.function = function
##        
##    def __get__(self, obj, cls = None):
##        return 
##
##    def __call__(self, *args, **kw):
##        return self.function(*args, **kw)
