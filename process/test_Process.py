import unittest
import Process
import os
import time
import socket
import pickle

from Process import thisProcess
from Listener import ConnectionPossibility, BrokenConnection

from test_multi_Process import timeout, TIMEOUT

class ProcessTest(unittest.TestCase):

    def test_equal(self):
        p1 = Process.Process('xx', 1,1,1)
        p2 = Process.Process('xx', 1,1,1)
        self.assertEquals(p1, p2)

    def test_notEqual(self):
        p1 = Process.Process('xx', 1,1,1)
        p2 = Process.Process('xxa', 1,1,1)
        self.assertNotEquals(p1, p2)
        self.assertNotEquals(p1, None)

value = None

def setValue(aValue):
    global value
    value = aValue


class MockListener1(object):
    
    listening = False
    p = 'not set'
    
    def listen(self):
        self.listening = True

    closed = False
    def close(self):
        self.closed = True

    def fromProcess(self, p):
        self.p = p

    def getConnectionPossibilities(self):
        return []



def loadProcess(id, process, args = (), kw = {}):

    return process(*args, **kw)

class MockProcess1(Process._ThisProcess):
    
    def getLoadFunction(self):
        return loadProcess

class ProcessClassAfterUnpickling1(Process.Process):
    pass

class MockProcess2(Process._ThisProcess):
    ProcessClassAfterUnpickling = ProcessClassAfterUnpickling1

            

class MockListener2(MockListener1):

    def getConnectionPossibilities(self):
        return [(setValue, (5,))]

dumpLoad = lambda o: pickle.loads(pickle.dumps(o))

class ThisProcessTest(unittest.TestCase):

    def test_hasPid(self):
        self.assertEquals(thisProcess.pid, os.getpid())

    def test_hostname(self):
        self.assertEquals(thisProcess.hostName, socket.gethostname())

    def test_ExecuteCall(self):
        thisProcess.call(setValue, ('1234',))
        self.assertEquals(value, '1234')
        thisProcess.call(setValue, ('12345',))
        self.assertEquals(value, '12345')

    def test_thisProcess_is_always_itself_here(self):
        self.assertIs(dumpLoad(thisProcess), thisProcess)

    def test_added_listener_will_listen(self):
        listener = MockListener1()
        self.assertFalse(listener.listening)
        thisProcess.addListener(listener)
        self.assertTrue(listener.listening)
        thisProcess.removeListener(listener)
        self.assertTrue(listener.closed)

    def test_new_thisProcess_does_not_infect_global_state(self):
        p = type(thisProcess)(thisProcess.identityString)
        self.assertNotEquals(p, Process.thisProcess)

    def test_process_is_set_to_listener(self):
        listener = MockListener1()
        thisProcess.addListener(listener)
        self.assertIs(listener.p, thisProcess)

    def test_dump_and_load_with_listener(self):
        setValue(3)
        p1 = MockProcess1('xx')
        l1 = MockListener2()
        p1.addListener(l1)
        p2 = dumpLoad(p1)
        self.assertEquals(p2._connectionPossibilities, [(setValue, (5,))])

    def test_class_after_load(self):
        self.assertNotEquals(
            dumpLoad(MockProcess2('33')).ProcessClassAfterUnpickling,
            MockProcess2('33').ProcessClassAfterUnpickling)

class MockConnection1(object):
    _to = None
    _from = None
    def isMockConnection(self):
        return True

    def fromProcess(self, _from):
        self._from = _from

    def toProcess(self, _from):
        self._to = _from

    def isProcess(self):
        return True

class MockQueue(object):
    @staticmethod
    def get(*args, **kw):
        return (lambda: None, (), {})

class ProcessInOtherProcess(Process.ProcessInOtherProcess):
    minimumConnectionTrySeconds = 0.1
    mock_dead = False

    def _emptyCallQueue(self, queue):
        Process.ProcessInOtherProcess._emptyCallQueue(self, queue)    
        self.mock_dead = True
            
class ProcessInOtherProcessTest(unittest.TestCase):

    def setUp(self):
        self.p = ProcessInOtherProcess('', 1,1,1)

    def assertIsDead(self):
        timeout(lambda:self.p.mock_dead, False)
        self.assertTrue(self.p.mock_dead)
        self.assertFalse(self.p.isAlive())

    def test_establishConnectionFails(self):
        self.p.addConnectionPossibility(ConnectionPossibility(setValue, (1,)))
        c = self.p.newConnection()
        self.assertEquals(c, None)
        self.assertEquals(value, 1)
        self.p.addConnectionPossibility(ConnectionPossibility(setValue, (2,)))
        self.p.addConnectionPossibility(ConnectionPossibility(setValue, (3,)))
        c = self.p.newConnection()
        self.assertEquals(c, None)
        self.assertEquals(value, 3)

    def test_establishConnectionWorks(self):
        self.p.addConnectionPossibility(ConnectionPossibility(setValue, (1,)))
        self.p.addConnectionPossibility(ConnectionPossibility(MockConnection1))
        self.p.newConnection()
        c = self.p.chooseConnection()
        self.assertTrue(c.isMockConnection())

    def test_connection_knows_about_endpoints(self):
        self.p.addConnectionPossibility(ConnectionPossibility(MockConnection1))
        self.p.newConnection()
        c = self.p.chooseConnection()
        self.assertEquals(c._from, thisProcess)
        self.assertEquals(c._to, self.p)
        
    def test_no_connection_can_be_established(self):
        self.p.call(setValue, ('x',))
        self.assertIsDead()
        self.assertNotEquals(value, 'x')

    def test_no_connection_can_be_established2(self):
        cp = ConnectionPossibility(BrokenConnection, ())
        self.p.addConnectionPossibility(cp)
        self.p.call(setValue, ('x',))
        self.assertIsDead()
        self.assertNotEquals(value, 'x')




class setConnectionEndpointsAlgorithmTest(unittest.TestCase):

    def setUp(self):
        if not thisProcess.getConnectionPossibilities():
            thisProcess.listenOnIPv4()

    def test_connection_toProcess_is_set_after_connecting(self):
        c = thisProcess.getConnectionPossibilities()[0]()
        for i in range(100):
            time.sleep(0.001)
            if c.toProcess().isProcess():
                break
        self.assertEquals(c.toProcess(), thisProcess)
        
    def test_connection_fromProcess_is_set_after_connecting(self):
        c = thisProcess.getConnectionPossibilities()[0]()
        for i in range(100):
            time.sleep(0.001)
            if c.fromProcess().isProcess():
                break
        self.assertEquals(c.fromProcess(), thisProcess)
        
if __name__ == '__main__':
    unittest.main(exit = False)
