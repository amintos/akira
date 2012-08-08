import unittest
from translation import *
from logic import *

class LogicTestCase(unittest.TestCase):

    def assertNoneSatisfies(self, iterable, condition):
        for each in iterable:
            if condition(each):
                self.fail("%s should not satisfy %s" %
                          (each, condition))

    def assertAnySatisfies(self, iterable, condition):
        for each in iterable:
            if condition(each):
                return
        self.fail("No element of %s satisfies %s" % (iterable, condition))

    def assertOneSatisfies(self, iterable, condition):
        satisfied = False
        for each in iterable:
            if condition(each):
                if satisfied:
                    self.fail("%s should not satisfy %s")


class NormalFormTest(unittest.TestCase):

    def test_atomic_fact(self):
        t = Theory().hold(Atom('a'))


