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

if __name__ == '__main__':
    unittest.main(exit = False)
