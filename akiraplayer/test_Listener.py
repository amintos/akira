import sys
import unittest
import time
import socket
import pickle
import thread

import Listener

from Listener import ConnectionPossibility

startedThreads = []
def thread_start_new(*args, **kw):
    id = thread.start_new(*args, **kw)
    startedThreads.append(id)
##    print '\nstarted_thread %i %s\n' % (id, args[0])
    return id

Listener.thread_start_new = thread_start_new


class SomeProcess(object):
    'save all connections created by listeners'
    _connections = []
    @classmethod
    def acceptedConnection(cls, conn):
        cls._connections.append(conn)

    @staticmethod
    def isProcess():
        return True

class ListenerTest(unittest.TestCase):

    def setUp(self):
        self.listener = Listener.Listener()
        self.listener.fromProcess(SomeProcess)
        self.listener.listen()
        
    def test_connectionPossibilities(self):
        poss = list(self.listener.getConnectionPossibilities())
        self.assertNotEquals(poss, [])

    def test_listening(self):
        self.assertTrue(self.listener.isListening())

    def test_close(self):
        self.listener.close()
        self.assertFalse(self.listener.isListening())

    def tearDown(self):
        self.listener.close()


def setValue(toValue):
    global value
    value = toValue


class CreateConnectionsTest(unittest.TestCase):

    ListenerClass = Listener.IPv4Listener

    def setUp(self):
        global value
        value = 'valueNotSet'
        self.listener = self.ListenerClass()
        self.listener.fromProcess(SomeProcess)
        self.listener.listen()
        self._connections = []

    def getConnection(self):
        conn = self.listener.getConnectionPossibilities()[0]()
        self._connections.append(conn)
        return conn
    
    def test_create_connection(self):
        connection = self.getConnection()

    def test_send_command_through_connection(self):
        connection = self.getConnection()
        thread.start_new(connection.call, (setValue, ('valueSet',), {}))
        i = 0
        for i in range(100):
            if value == 'valueSet':
                break
            time.sleep(0.001)
        self.assertEquals(value, 'valueSet')

    def test_connectionPossibilities_can_be_pickled(self):
        poss = self.listener.getConnectionPossibilities()
        self.assertEquals(dumpLoad(poss), poss)

    def tearDown(self):
        self.listener.close()
        for conn in self._connections + SomeProcess._connections:
            conn.close()



testOthers = True
if Listener.has_pipe and testOthers and False:
    class PipeTest(CreateConnectionsTest):
        ListenerClass = Listener.PipeListener

if Listener.has_unix and testOthers:
    class UnixTest(CreateConnectionsTest):
        ListenerClass = Listener.UnixListener

if Listener.has_ipv6 and testOthers:
    class IPv6Test(CreateConnectionsTest):
        ListenerClass = Listener.IPv6Listener

        def test_listeners_address_is_colonColon(self):
            self.assertEquals(self.listener.listener.address[0], '::')
        

class IPv4Test(CreateConnectionsTest):

    def test_listeners_address_is_0000(self):
        self.assertEquals(self.listener.listener.address[0], '0.0.0.0')

class IPv4Test1(unittest.TestCase):

    port = 2345
    def setUp(self):
        self.port += 1
        self.address = ('127.0.0.1', self.port)
        self.listener = Listener.IPv4Listener(self.address)
        self.listener.fromProcess(SomeProcess)
        self.listener.listen()

    def test_getAddress(self):
        p = self.listener.getConnectionPossibilities()[0]
        function, args = p.function, p.args
        self.assertIn(self.address, args)

    def test_socket_listens(self):
        import socket
        s = socket.socket()
        s.settimeout(3)
        s.connect(self.address)
        s.close()
        self.assertTrue(self.listener.isListening())

    def tearDown(self):
        self.listener.close()

        
def g(a, b = 1):
    return a, b

def dumpLoad(o):
    return pickle.loads(pickle.dumps(o))


class ConnectionPossibilityTest(unittest.TestCase):

    def setUp(self):
        self.c = ConnectionPossibility(g, (1,), {'b': 2})

    def test_reduce(self):
        c = self.c
        c2 = dumpLoad(c)
        self.assertEquals(c2.args, c.args)
        self.assertEquals(c2.kw, c.kw)
        self.assertEquals(c2.function, c.function)

    def test_call(self):
        self.assertEquals(self.c(), (1, 2))

class ConnectionPickleTest(unittest.TestCase):

    def test_equal_after_pickle(self):
        c = Listener.BaseConnection()
        with c:
            self.assertEquals(dumpLoad(c), c)

    def test_cannnot_be_pickled_by_other_connection(self):
        c1 = Listener.BaseConnection()
        c2 = Listener.BrokenConnection()
        with c2:
            self.assertRaises(Listener.ConnectionMustBeTop, lambda: c1.__reduce__())

    def test_connection_becomes_other_connection_when_unpickled(self):
        c1 = Listener.BaseConnection()
        c2 = Listener.BrokenConnection()
        with c1:
            s = pickle.dumps(c1)
        with c2:
            c2_ = pickle.loads(s)
        self.assertEquals(c2_, c2)

    def test_connection_cannot_be_pickled_if_not_top(self):
        c1 = Listener.BaseConnection()
        self.assertRaises(Listener.ConnectionMustBeTop, lambda: pickle.dumps(c1))

class removeDuplicatesTest(unittest.TestCase):

    def test_1234(self):
        self.assertEquals(Listener.removeDuplicates([1,2,3,4]), [1,2,3,4])

    def test_1(self):
        self.assertEquals(Listener.removeDuplicates([2,1,3,2,4,1,4,3]), [2,1,3,4])

       

if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
    if False:
        import sys
        time.sleep(0.1) # wait for threads to die
        print 'frames:', len(sys._current_frames().items())
        print 'connections:', len(SomeProcess._connections)
        for connection in SomeProcess._connections:
            connection.close()
        time.sleep(5) # wait for threads to die
        for k in sorted(sys._current_frames()):
            f = sys._current_frames()[k]
            
            if k in startedThreads:
                print f.f_code.co_filename,
                print k, f.f_code.co_firstlineno
            else:
                print
        print 'frames:', len(sys._current_frames().items())
