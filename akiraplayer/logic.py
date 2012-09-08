from collections import defaultdict


def toVariableName(string):
    if string.isalnum():
        return string + '_'
    return string.encode('hex')

def ident(string):
    return string.replace('\n', '\n    ')



class TheoryMethod(list):

    def __init__(self, theory):
        self._theory = theory
        list.__init__(self)

    @property
    def name(self):
        return self[0].functor

    @property
    def argumentString(self):
        return self[0].argumentString

    def __call__(self, *args):
        for term in self:
            term.match(self._theory, *args)


    def compiled(self):
        s = 'def %s(%s):\n    ' % (toVariableName(self.name), \
                                   self.argumentString)
        l = [ident(term.compiled()) for term in self]
        return s + '\n    '.join(l)
    
class Theory(object):

    def newTheoryMethod(self):
        return TheoryMethod(self)

    def __init__(self, gdl):
        self.gdl = gdl
        self.statements = defaultdict(self.newTheoryMethod) # { predicate : statement }
        for gdl_statement in gdl:
            term = Term.from_gdl(gdl_statement)
            self.statements[term.functor].append(term)
        self.functions ={}
        
        exec self.compiled() in self.functions

    @property
    def methods(self):
        return self.statements.values()

    def compiled(self):
        return '\n'.join(map(lambda method: method.compiled(), self.methods))


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
        callbackValues = ', '.join([atom.compiled() for atom in self.args])
        return 'if %s: callback(%s)' % (' and '.join(ands), \
                                        callbackValues)
    @property
    def callbackArguments(self):
        return ['a%i' % i for i in range(1, len(self.args) + 1)]

    @property
    def argumentNames(self):
        return self.callbackArguments + ['callback']

    @property
    def argumentString(self):
        return ', '.join(self.argumentNames)

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

    @staticmethod
    def from_gdl(gdl):
        return Rule(Term.from_gdl(gdl[1]), map(Term.from_gdl, gdl[2:]))

    def match(self, theory, *args):
        print self.body

    def compiled(self):
        pass

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
        self.__dict__ = theory.methodDictionairy
    
class _:
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False
    def __repr__(self):
        return '_'

_ = _()


__all__ = ['_', 'logic', 'Theory', 'Term', 'Rule', 'Variable', 'Or', 'Atom', \
           'Not', 'toVariableName']
