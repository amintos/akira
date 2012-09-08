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
        l = []
        for arg in args:
            assert arg.isAtom()
            l.append(arg.functor)
        self.values.append(tuple(l))

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
        self.assertEvaluated([('2',)])        
        
    def test_get_successor_nothing(self):
        self.logic.s('nothing', _, self.c)
        self.assertEvaluated([])

    def test_get_inverse_successor(self):
        self.logic.s(_, '4', self.c)
        self.assertEvaluated([('3',)])
        
    def test_verify_successor(self):
        self.logic.s('3', '4', self.c)
        self.assertEvaluated([()])
        
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

    code = '''(s 1 1 a) (s 2 3 a) (s 3 6 a)'''

    def test_0_is_not_included(self):
        self.logic.s('0', _, _, self.c)
        self.assertEvaluated([])

    def test_1(self):
        self.logic.s('1', '1', _, self.c)
        self.assertEvaluated([('a',)])

    def test_all_elements(self):
        self.logic.s(_, _, 'a', self.c)
        self.assertEvaluated(set([('1', '1'), ('2', '3'), ('3', '6')]))


##class MatchTest(unittest.TestCase):
##
##    def test_atom_matches_itself(self):
##        a = Atom('a')
##        self.assertTrue(a.matches(a))
##        self.assertTrue(a.matches(Atom(a)))
        
if __name__ == '__main__':
    dT = None; 'SumTest'
    unittest.main(defaultTest = dT, exit = False)
