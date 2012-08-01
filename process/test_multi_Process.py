import unittest
import time
from multiprocessing.pool import Pool

from Process import thisProcess

TIMEOUT = 5

def timeout(functionToBoolean, timeout = TIMEOUT):
    w_reference = functionToBoolean()
    t = time.time() + timeout
    while t > time.time():
        w = functionToBoolean()
        if w != w_reference:
            break
        time.sleep(0.001)

value = None
def setValue(aValue):
    global value
    value = aValue

thisProcess.listenWhereYouCan()

class CommunicateTest(unittest.TestCase):

    def setUp(self):
        global value
        self.pool = Pool()
        value = None

    def test_value_is_not_set(self):
        self.assertEquals(value, None)

    def test_send_to_other_side_and_call_back(self):
        self.pool.apply_async(thisProcess.call, (setValue, ('aValue',)))
        timeout(lambda: value is None)
        self.assertEquals(value, 'aValue')


if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
