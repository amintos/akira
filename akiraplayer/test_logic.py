import unittest
from logic import *

def getIdent(line):
    i = 0
    while i < len(line) and line[i] in ' \r\t':
        i += 1
    return i

def normalizeSource(string):
    assert not '\t' in string
    final = []
    for line in string.split('\n'):
        if len(line) == getIdent(line):
            continue
        final.append(line)
    return '\n'.join(final)
    
    

class TermInterpretationTest(unittest.TestCase):

    def test_atom(self):
        a = Term.from_gdl('a')
        self.assertIsInstance(a, Atom)
        self.assertEqual('a', a.functor)

    def test_variable(self):
        v = Term.from_gdl('?v')
        self.assertIsInstance(v, Variable)
        self.assertEqual('v', v.functor)

    def test_compound(self):
        c = Term.from_gdl(('f', 'a', 'b'))
        self.assertEqual(c.functor, 'f')
        self.assertEqual(c.args[0].functor, 'a')
        self.assertEqual(c.args[1].functor, 'b')

    def test_or(self):
        c = Term.from_gdl(('or', 'a', 'b'))
        self.assertIsInstance(c,Or)
        self.assertEqual(c.t1.functor, 'a')
        self.assertEqual(c.t2.functor, 'b')

    def test_not(self):
        n = Term.from_gdl(('not', 'a'))
        self.assertIsInstance(n, Not)
        self.assertEqual(n.t1.functor, 'a')

    def test_rule(self):
        r = Term.from_gdl(('<=', ('a', '?x'), ('b', '?x'), ('c', '?x')))
        self.assertIsInstance(r, Rule)
        self.assertEqual(r.head.functor, 'a')
        self.assertEqual(2, len(r.body))
        self.assertEqual(r.body[0].functor, 'b')
        self.assertEqual(r.body[1].functor, 'c')

    def test_theory(self):
        f = (
            ('a', 'b'),
            ('a', 'c'),
            ('<=', ('b', '?x'), ('a', '?x'))
        )
        t = Theory(f)
        self.assertEqual(2, len(t.statements))
        self.assertIn('a', t.statements)
        self.assertIn('b', t.statements)
        self.assertEqual('a', t.statements['b'][0].body[0].functor)


class LogicTest(unittest.TestCase):

    code = ''

    def setUp(self):
        self.logic = logic.fromString(self.code)
        self.values = []
        
    def c(self, *args):
        self.values.append(args)

    def assertEvaluated(self, expectedValues):
        self.assertEquals(set(self.values), set(expectedValues))

class SuccessorTest(LogicTest):

    code = '''
(s 1 2)
(s 2 3)
(s 3 4)
(s 4 5)
(s 5 6)
'''

    def test_get_successor_1(self):
        self.logic.s('1', _, self.c)
        self.assertEvaluated([('1', '2',)])        
        
    def test_get_successor_nothing(self):
        self.logic.s('nothing', _, self.c)
        self.assertEvaluated([])

    def test_get_inverse_successor(self):
        self.logic.s(_, '4', self.c)
        self.assertEvaluated([('3','4')])
        
    def test_verify_successor(self):
        self.logic.s('3', '4', self.c)
        self.assertEvaluated([('3', '4')])
        
    def test_all_successors(self):
        self.logic.s(_, _, self.c)
        expectedValues = set([(str(x), str(x + 1)) for x in range(1, 6)])
        self.assertEquals(set(self.values), expectedValues)

class PredecessorTest(SuccessorTest):
    code = SuccessorTest.code + '''

(<= (p ?x ?y) (s ?y ?x))

'''

    def test_predecessor_of_1(self):
        self.logic.p('1', _, self.c)
        self.assertEvaluated([])

    def test_predecessor_of_2(self):
        self.logic.p('2', _, self.c)
        self.assertEvaluated([('2','1')])

    def test_predecessor_equals_successor(self):
        def f(x, y):
            l = []
            def g(*args):
                l.append('called')
            self.logic.s(y, x, g)
            self.assertEquals(l, ['called'])
        for i in range(1, 6):
            self.logic.p(_, _, f)

    def test_p_yields_all_values(self):
        self.logic.p(_, _, self.c)
        expectedValues = set([(str(x + 1), str(x)) for x in range(1, 6)])
        self.assertEquals(set(self.values), expectedValues)

    def test_replace_underscore(self):
        global _
        import logic as l
        a = _
        try:
            l._ = _ = object()
            self.test_predecessor_of_1()
        finally:
            l._ = _ = a

class SumTest(LogicTest):

    code = ''' (s 1 1 a) (s 2 3 a) (s 3 6 a)'''

    def test_0_is_not_included(self):
        self.logic.s('0', _, _, self.c)
        self.assertEvaluated([])

    def test_1(self):
        self.logic.s('1', '1', _, self.c)
        self.assertEvaluated([('1','1','a',)])

    def test_all_elements(self):
        self.logic.s(_, _, 'a', self.c)
        self.assertEvaluated(set([('1','1','a'),('2','3','a'),('3','6','a')]))

def hexform(*args):
    d = {}
    for a in args:
        d[a] = a.encode('hex')
    return d

class CompileTest(unittest.TestCase):

    def assertSourceEquals(self, source, expected):
        sourceLines = normalizeSource(source).split('\n')
        expectedLines = normalizeSource(expected).split('\n')
        line = 0
        for sourceLine, expectedLine in zip(sourceLines, expectedLines):
            line += 1
            char = 0
            for sourceChar, expectedChar in zip(sourceLine, expectedLine):
                self.assertEquals(sourceChar, expectedChar, 'Sources shall be'\
                                  ' equal:\n'\
                                  '---- in ---- \n%s\n---- expected ----\n%s\n'\
                                  '---- in line %i ----\n%s\n%s\n%s' % (\
                                      source, expected, line, sourceLine, \
                                      expectedLine, ' ' * char + '^'))
                char += 1

    def test_nothing(self):
        t = Theory(())
        self.assertSourceEquals(t.compiled(), '')

    def test_a(self):
        t = Theory((('a',),))
        self.assertSourceEquals(t.compiled(), '''def a_(callback):
    callback()''')

    def test_atom(self):
        self.assertEquals(Atom('asdfa').compiled(), '"asdfa_"')
        
    def test_variable(self):
        self.assertEquals(Variable('asdfa').compiled(), 'asdfa_')
        
    def test_variable_special(self):
        self.assertEquals(Variable('\asdfa\\_').compiled(), \
                          '\asdfa\\_'.encode('hex'))
        
    def test_one_argument(self):
        t = Theory((('a', 'b'),))
        self.assertSourceEquals(t.compiled(), '''def a_(a1, callback):
    if a1 == "b_": callback("b_")''')

    def test_execute(self):
        t = Theory((('a', 'b'),))
        l = []
        t.functions['a_']('b_', l.append)
        self.assertEquals(l, ['b_'])
        t.functions['a_'](_, l.append)
        self.assertEquals(l, ['b_'] * 2)
        
    def test_one_argument2(self):
        t = Theory((('a', 'b'), ('a', 'c'),))
        self.assertSourceEquals(t.compiled(), '''def a_(a1, callback):
    if a1 == "b_": callback("b_")
    if a1 == "c_": callback("c_")''')
        l = []
        t.functions['a_']('b_', l.append)
        self.assertEquals(l, ['b_'])
        t.functions['a_'](_, l.append)
        self.assertEquals(l, ['b_'] * 2 + ['c_'])
    
    def test_three_arguments(self):
        t = Theory((('a', 'b', 'c', 'd'),))
        self.assertSourceEquals(t.compiled(), '''def a_(a1, a2, a3, callback):
    if a1 == "b_" and a2 == "c_" and a3 == "d_": callback("b_", "c_", "d_")''')


    def test_rule_with_one_term(self):
        t = Theory((('<=', ('a', 'b'), ('b', 'x')), ('b', 'x')))
        self.assertSourceEquals(t.compiled(), '''def a_(a1, callback):
    def callback_(a1):
        assert (a1,) == ("x_",)
        callback("b_")
    b_("x_", callback_)
def b_(a1, callback):
    if a1 == "x_": callback("x_")''')
        l = []
        t.functions['a_'](_, l.append)
        self.assertEquals(l, ["b_"])

    def test_rule_with_one_term2(self):
        t = Theory((('<=', ('a', 'b'), ('b', 'x')), ('b', 'y')))
        l = []
        t.functions['a_'](_, l.append)
        self.assertEquals(l, [])

    def assertEvaluates(self, theory, function, result):
        l = []
        theory.functions[function](_, l.append)
        self.assertEquals(l, result)
   
    def test_rule_with_two_terms_false_true(self):
        t = Theory((('<=', ('a', 'b'), ('b', 'x'), ('f', 'a')), \
                    ('f', 'a'), ('b', 'y')))
        self.assertEvaluates(t, 'a_', [])

    def test_rule_with_two_terms_true_true(self):
        t = Theory((('<=', ('a', 'b'), ('b', 'y'), ('f', 'a')), \
                    ('f', 'a'), ('b', 'y')))
        self.assertEvaluates(t, 'a_', ['b_'])

    def test_rule_with_two_terms_false_true(self):
        t = Theory((('<=', ('a', 'b'), ('b', 'y'), ('f', 'a')), \
                    ('f', 'b'), ('b', 'y')))
        self.assertEvaluates(t, 'a_', [])

    def test_rule_with_two_terms_false_false(self):
        t = Theory((('<=', ('a', 'b'), ('b', 'y'), ('f', 'a')), \
                    ('f', 'b'), ('b', 'x')))
        self.assertEvaluates(t, 'a_', [])

    def test_rule_with_no_terms(self):
        t = Theory((('<=', ('f', 'g'), ), \
                    ('f', 'b'), ('b', 'x')))
        self.assertEvaluates(t, 'f_', ['g_', 'b_'])
        
    def test_variable_conversion(self):
        self.assertBidirectionalVariableConversion('test!random')
        self.assertBidirectionalVariableConversion('a')
        self.assertBidirectionalVariableConversion(''.join(map(chr, range(256))))

    def assertBidirectionalVariableConversion(self, string):
        self.assertEquals(fromVariableName(toVariableName(string)), string)

##    def test_three_jump_dependency(self):
##        t = Theory((('<=', ('a','?x'), ('b','?x','?x')), \
##                   (('<=', ('b','?x','?y'), ('c','?x'), ('c','?y')))
        

class _Test(unittest.TestCase):
    def test_equal_right(self):
        self.assertTrue(_ == 1)
        self.assertTrue(_ == 'ajhsdfk')
        
    def test_equal_left(self):
        self.assertTrue(1 == _)
        self.assertTrue('ajhsdfk' == _)
        
if __name__ == '__main__':
    dT = None;'_Test';None;'CompileTest';None; 'SumTest'
    unittest.main(defaultTest = dT, exit = False)

