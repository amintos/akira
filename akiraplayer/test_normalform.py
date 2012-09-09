from testing import *
from normalform import *
from logic import *


class NormalFormTest(LogicTestCase):

    def test_atomic_fact(self):
        t = Theory().hold(Atom('a')).hold(Atom('b'))
        self.fail("TODO")


