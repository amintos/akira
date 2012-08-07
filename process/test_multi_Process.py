import unittest
import time
from multiprocessing.pool import Pool

from Process import thisProcess
from pickle import PicklingError

TIMEOUT = 5
_l = []
def timeout(functionToBoolean, value_reference = _l, timeout = TIMEOUT):
    if value_reference is _l:
        value_reference = functionToBoolean()
    t = time.time() + timeout
    while t > time.time():
        value = functionToBoolean()
        if value != value_reference:
            break
        time.sleep(0.001)
    else:
        print 'timed out'

value = None
def setValue(aValue):
    global value
    value = aValue


def sendArgsBack((toProcess, args)):
    toProcess.call(recieveArgs,(thisProcess, args))
    time.sleep(0.1) ## let other processes pull from queue
##    timeout(toProcess in thisProcess.knownProcesses, False)
##    assert toProcess in thisProcess.knownProcesses


answers = []
PROCESS = 0
ARGS = 1
def recieveArgs(fromProcess, args):
    answers.append((fromProcess, args))
    
thisProcess.listenWhereYouCan()
    
class CommunicateTest(unittest.TestCase):

    PROCESSES = 4

    def setUp(self):
        global value
        self.pool = Pool(self.PROCESSES)
        value = None

    def tearDown(self):
        self.pool.terminate()
        self.pool.close()

    def test_value_is_not_set(self):
        self.assertEquals(value, None)

    def test_send_to_other_side_and_call_back(self):
        self.pool.apply_async(thisProcess.call, (setValue, ('aValue',)))
        timeout(lambda: value is None)
        self.assertEquals(value, 'aValue')

##    @unittest.skip('the error is raised in another thread')
##    def test_send_an_not_executed_here(self):
##        def setValue(v):
##            self.fail('called')
##        self.assertRaises(PicklingError, 
##            lambda: self.pool.apply_async(thisProcess.call, (setValue, ('aValue',))))

    def test_the_processes_get_to_know_another(self):
        l = [(thisProcess, i) for i in range(self.PROCESSES)]
        noneList = self.pool.map(sendArgsBack, l)
        self.assertEquals(noneList, [None] * len(l))
        timeout(lambda: len(thisProcess.knownProcesses) >= self.PROCESSES, False)
        self.assertGreaterEqual(len(thisProcess.knownProcesses), self.PROCESSES)
        for process, arg in answers:
            self.assertIn(process, thisProcess.knownProcesses)
        set1 = lambda: set([t[ARGS] for t in answers])
        rightSet = set(range(self.PROCESSES))
        ## todo: following line failed once - i do not know why
        timeout(lambda: rightSet == set1(), False)
        self.assertEquals(set1(), rightSet, 'all processes communicated back')


if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
