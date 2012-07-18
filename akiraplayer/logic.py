from collections import defaultdict

class Theory(object):

    def __init__(self, gdl):
        self.statements = defaultdict(lambda: [])   # { predicate : statement }
        for gdl_statement in gdl:
            term = Term.from_gdl(gdl_statement)
            self.statements[term.functor].append(term)

# -----------------------------------------------------------------------------
# TERMS


class Term(object):

    def __init__(self, functor):
        self.functor = functor
        self.arity = 0

    @staticmethod
    def from_gdl(gdl):
        if isinstance(gdl, str):
            return Atom.from_gdl(gdl)
        else:
            return CompoundTerm.from_gdl(gdl)

# -----------------------------------------------------------------------------
# 0-ARY TERMS

class Atom(Term):

    def __init__(self, name):
        Term.__init__(self, name)

    def data(self):
        return self.functor

    @staticmethod
    def from_gdl(gdl):
        if gdl.startswith('?'):
            return Variable(gdl[1:])
        else:
            return Atom(gdl)


class Variable(Atom):

    def data(self):
        return '?%s' % self.functor

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