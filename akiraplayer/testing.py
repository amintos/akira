#
#   Module providing extended testing facilities
#

import unittest

class LogicTestCase(unittest.TestCase):

    def assertNoneSatisfy(self, iterable, condition):
        for each in iterable:
            if condition(each):
                self.fail("%s should not satisfy %s" %
                          (each, condition))

    def assertAnySatisfy(self, iterable, condition):
        for each in iterable:
            if condition(each):
                return
        self.fail("No element of %s satisfies %s" % (iterable, condition))

    def assertOneSatisfy(self, iterable, condition):
        satisfied = False
        last_satisfied = None
        for each in iterable:

            if condition(each):
                if satisfied:
                    self.fail("%s should no longer satisfy %s as %s did" %
                              (each, condition, last_satisfied))
                else:
                    satisfied = True
                    last_satisfied = each

        if not satisfied:
            self.fail("No element of %s satisfies %s" % (iterable, condition))

    def assertAllSatisfy(self, iterable, condition):
        for each in iterable:
            if not condition(each):
                self.fail("%s should satisfy %s" % (each, condition))


