from collections import defaultdict

def toVariableName(string):
    if string.isalnum():
        return string + '_'
    return string.encode('hex')

def fromVariableName(string):
    if string.endswith('_'):
        return string[:-1]
    return string.decode('hex')

def ident(string):
    return '    ' + string.replace('\n', '\n    ')


class TheoryMethod(list):

    def __init__(self, theory):
        self._theory = theory
        list.__init__(self)

    @property
    def name(self):
        return self[0].functor

    @property
    def compiledName(self):
        return self[0].compiledName

    @property
    def argumentString(self):
        return self[0].argumentString

    def __call__(self, *args):
        for term in self:
            term.match(self._theory, *args)

    def compiled(self):
        s = 'def %s(%s):\n' % (self.compiledName, \
                                   self.argumentString)
        l = [ident(term.compiled()) for term in self]
        return s + '\n'.join(l)

class TheoryLoader(object):
    def __init__(self, source):
        self.source = source

    def get_source(self, name):
        return self.source

class Theory(object):

    toVariableName = toFunctionName = staticmethod(toVariableName)

    def newTheoryMethod(self):
        return TheoryMethod(self)

    @property
    def methodDictionairy(self):
        return TheoryMethodDictionairy(self)

    def __init__(self, gdl = (), debug = 1):
        self.debug = debug
        self.gdl = gdl
        self.statements = defaultdict(self.newTheoryMethod) # { predicate : statement }
        for gdl_statement in gdl:
            self.hold(Term.from_gdl(gdl_statement))
        self.functions = self.getFunctions()

    def getFunctions(self):
        functions = {}
        if self.debug:functions['__name__'] = name = 'Theory%s' % id(self)
        source = self.compiled()
        try:
            code = compile(source, name, 'exec')
            exec code in functions
        except:
            print source
            raise
        if self.debug:
            functions['__loader__'] = TheoryLoader(source)
            import linecache
            linecache.updatecache(name, functions)
        return functions

    @property
    def methods(self):
        return self.statements.values()

    def compiled(self):
        return '\n'.join(map(lambda method: method.compiled(), self.methods))

    def hold(self, term):
        self.statements[term.functor].append(term)
        return self

    def getFunction(self, name, default = None):
        l = []
        func = self.functions.get(toVariableName(name), l)
        if func is l:
            return default
        def ret(*args):
            assert args, 'callback is the last argument'
            callback = args[-1]
            assert callable(callback), 'the callback must be callable'
            args = args[:-1]
            newArgs = []
            for arg in args:
                assert isinstance(arg, basestring) or arg is _, \
                       'all arguments must be either _ or a string'
                if arg is _:
                    newArgs.append(_)
                else:
                    newArgs.append(toVariableName(arg))
            def cb(*args):
                callback(*map(fromVariableName, args))
            newArgs.append(cb)
            func(*newArgs)
        return ret

# -----------------------------------------------------------------------------
# TERMS

class Term(object):

    def __init__(self, functor):
        self.functor = functor
        self.arity = 0

    def isAtom(self):
        return False

    @staticmethod
    def from_gdl(gdl):
        if isinstance(gdl, str):
            return Atom.from_gdl(gdl)
        else:
            return CompoundTerm.from_gdl(gdl)

    def match(self, theory, *args):
        raise NotImplementedError('to be implemented in subclasses')

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.functor)

# -----------------------------------------------------------------------------
# 0-ARY TERMS

class Atom(Term):

    def __init__(self, name):
        Term.__init__(self, name)

    def isAtom(self):
        return True

    def data(self):
        return self.functor

    @staticmethod
    def from_gdl(gdl):
        if gdl.startswith('?'):
            return Variable(gdl[1:])
        else:
            return Atom(gdl)

    def match(self, theory, a, cb):
        if a is _:
            cb(self.functor)
        elif a == self.functor:
            cb()

    def __eq__(self, other):
        return other == self.functor

    def __ne__(self, other):
        return not self == other

    def compiled(self):
        return '"%s"' % toVariableName(self.functor)


class Variable(Term):

    def data(self):
        return '?%s' % self.functor

    def compiled(self):
        return toVariableName(self.functor)

# -----------------------------------------------------------------------------
# N-ARY TERMS

class CompoundTerm(Term):

    def __init__(self, functor, args):
        Term.__init__(self, functor)
        self.args = args
        self.arity = len(args)

    def data(self):
        return (self.functor,) + tuple(map(lambda x: x.data, self.args))

    @staticmethod
    def from_gdl(gdl):
        functor = gdl[0]
        if functor in TERM_CLASSES:
            return TERM_CLASSES[functor].from_gdl(gdl)
        else:
            return CompoundTerm(functor, map(Term.from_gdl, gdl[1:]))

    def match(self, theory, *args):
        cb = args[-1]
        args = args[:-1]
        v = []
        for arg1, arg2 in zip(self.args, args):
            assert arg1.isAtom(), '%s is no atom' % (arg1,)
            if arg2 is _:
                v.append(arg1)
            elif arg1 != arg2:
                print repr(arg1), '!=', repr(arg2)
                break
        else:
            cb(*v)

    def __repr__(self):
        return '<%s %s: %s>' % (self.__class__.__name__, self.functor, \
                                ','.join(map(repr, self.args)))

    def compiled(self):
        if not self.args:
            return 'callback()'
        assert all(map(lambda a: a.isAtom(), self.args)), 'no variables allowed'
        ands = ['%s == %s' % (argumentName, self.args[i].compiled()) \
                for i, argumentName in enumerate(self.callbackArguments)]
        return 'if %s: callback(%s)' % (' and '.join(ands), \
                                        self.callbackValueString)
    @property
    def callbackArguments(self):
        return ['a%i' % i for i in range(1, len(self.args) + 1)]

    @property
    def callbackArgumentString(self):
        return ', '.join(self.callbackArguments)

    @property
    def argumentNames(self):
        return self.callbackArguments + ['callback']

    @property
    def argumentString(self):
        return ', '.join(self.argumentNames)

    @property
    def compiledName(self):
        return toVariableName(self.functor)

    @property
    def callbackValueString(self):
        return ', '.join([atom.compiled() for atom in self.args])

    def calling(self, callback):
        cba = self.callbackValueString
        if cba:
            args = cba + ', ' + callback
        else:
            args = callback
        return '%s(%s)' % (self.compiledName, args)

class BinaryTerm(CompoundTerm):

    def __init__(self, functor, t1, t2):
        CompoundTerm.__init__(self, functor, (t1, t2))
        self.t1 = t1
        self.t2 = t2

    def data(self):
        return self.functor, t1.data(), t2.data()


class Or(BinaryTerm):

    def __init__(self, t1, t2):
        BinaryTerm.__init__(self, 'or', t1, t2)

    @staticmethod
    def from_gdl(gdl):
        return Or(Term.from_gdl(gdl[1]), Term.from_gdl(gdl[2]))



class Not(CompoundTerm):
    # Refactor to inherit from a new class UnaryTerm if necessary

    def __init__(self, term):
        CompoundTerm.__init__(self, 'not', (term,))
        self.t1 = term

    @staticmethod
    def from_gdl(gdl):
        return Not(Term.from_gdl(gdl[1]))


class Rule(CompoundTerm):

    def __init__(self, head, body):
        CompoundTerm.__init__(self, head.functor, (head,) + tuple(body))
        self.head = head
        self.body = body

    @property
    def callbackArguments(self):
        return self.head.callbackArguments

    @property
    def argumentNames(self):
        return self.head.argumentNames

    @property
    def argumentString(self):
        return self.head.argumentString

    @property
    def callbackValueString(self):
        return self.head.callbackValueString

    @staticmethod
    def from_gdl(gdl):
        return Rule(Term.from_gdl(gdl[1]), map(Term.from_gdl, gdl[2:]))

    def match(self, theory, *args):
        print self.body

    def compiled(self):
        all = ''
        callback = 'callback(%s)\n' % self.callbackValueString
        for element in self.body:
            cas = element.callbackArgumentString
            s = 'def callback_(%s):\n' % cas
            s += ident('assert (%s,) == (%s,)\n%s' % (cas, element.callbackValueString, \
                                                      all))
            s += callback
            callback = element.calling('callback_')
            all = s
        all += '\n' + callback
        return all

# -----------------------------------------------------------------------------
# Mapping from special functors to term subclasses

TERM_CLASSES = {
    '<='    : Rule,
    'or'    : Or,
    'not'   : Not,

    # GDL keywords -- specialize if necessary
    'true'  : CompoundTerm,
    'init'  : CompoundTerm,
    'legal' : CompoundTerm,
    'next'  : CompoundTerm,
    'does'  : CompoundTerm,
}

# -----------------------------------------------------------------------------
#

class logic(object):
##    def s(self, x, y, c):
##        if x == 'nothing' or y == '1':
##            return 
##        if x is not _ and y is not _:
##            if int(x) - int(y) == -1:
##                c()
##        elif x is _ and y is not _:
##            c(str(int(y) - 1))
##        elif y is _ and x is not _:
##            c(str(int(x) + 1))
##        else:
##            for i in range(1, 6):
##                c(str(i), str(i + 1))
##
##    def p(self, x, y, c):
##        if x == y == _:
##            _c = c
##            c = lambda x, y: _c(y, x)
##        self.s(y, x, c)

    #
    # class side constuctor
    #

    theoryFromGdl = Theory
    
    @classmethod
    def fromString(cls, string):
        import kif
        gdl = kif.parse(string)
        return cls.fromGdl(gdl)

    @classmethod
    def fromGdl(cls, gdl):
        theory = cls.theoryFromGdl(gdl)
        return cls.fromTheory(theory)

    @classmethod
    def fromTheory(cls, theory):
        return cls(theory)

    #
    # functions
    #

    def __init__(self, theory):
        self.theory = theory

    def __getattr__(self, name):
        if name == 'theory':
            return self.__dict__['theory']
        l = []
        ret = self.theory.getFunction(name, l)
        if ret is l:
            raise AttributeError('%s is not a function os me!' % (name,))
        return ret
class _:
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False
    def __repr__(self):
        return '_'

_ = _()


__all__ = ['_', 'logic', 'Theory', 'Term', 'Rule', 'Variable', 'Or', 'Atom', \
           'Not', 'toVariableName', 'fromVariableName']
