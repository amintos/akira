import unittest
from logic import *

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
        self.assertEvaluated([('1',)])

    def test_predecessor_equals_successor(self):
        def f(x, y):
            l = []
            def g():
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

    def test_nothing(self):
        t = Theory(())
        self.assertEquals(t.compiled(), '')

    def test_a(self):
        t = Theory((('a',),))
        self.assertEquals(t.compiled(), '''def a_(callback):
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
        self.assertEquals(t.compiled(), '''def a_(a1, callback):
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
        self.assertEquals(t.compiled(), '''def a_(a1, callback):
    if a1 == "b_": callback("b_")
    if a1 == "c_": callback("c_")''')
        l = []
        t.functions['a_']('b_', l.append)
        self.assertEquals(l, ['b_'])
        t.functions['a_'](_, l.append)
        self.assertEquals(l, ['b_'] * 2 + ['c_'])
    
    def test_three_arguments(self):
        t = Theory((('a', 'b', 'c', 'd'),))
        self.assertEquals(t.compiled(), '''def a_(a1, a2, a3, callback):
    if a1 == "b_" and a2 == "c_" and a3 == "d_": callback("b_", "c_", "d_")''')


    def test_rule_with_one_term(self):
        t = Theory((('<=', ('a', 'b'), ('b', 'x')), ('b', 'x')))
        self.assertEquals(t.compiled(), '''def a_(a1, callback):
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
        

        
if __name__ == '__main__':
    dT = None;'CompileTest';None; 'SumTest'
    unittest.main(defaultTest = dT, exit = False)

