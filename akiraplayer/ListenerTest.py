import sys
import unittest
import time
import socket

import Listener

class ListenerTest(unittest.TestCase):

    def setUp(self):
        self.listener = Listener.Listener()
        self.listener.listen()
        
    def test_connectionPossibilities(self):
        poss = list(self.listener.getConnectionPossibilities())
        self.assertNotEquals(poss, [])

    def test_listening(self):
        self.assertTrue(self.listener.isListening())

    def test_close(self):
        self.listener.close()
        self.assertFalse(self.listener.isListening())


def setValue(toValue):
    global value
    value = toValue

class CreateConnectionsTest(unittest.TestCase):

    ListenerClass = Listener.IPv4Listener

    def setUp(self):
        global value
        value = 'notSet'
        self.listener = self.ListenerClass()
        self.listener.listen()

    def getConnection(self):
        return apply(*self.listener.getConnectionPossibilities()[0])

    
    def test_create_connection(self):
        connection = self.getConnection()
        connection.close()

    def test_set_value(self):
        connection = self.getConnection()
        connection.call(setValue, (4,), {})
        i = 0
        while i < 100 and value != 4:
            time.sleep(0.001)
        self.assertEquals(value, 4)
        connection.close()


testOthers = True
if Listener.has_pipe and testOthers:
    class PipeTest(CreateConnectionsTest):
        ListenerClass = Listener.PipeListener

if Listener.has_unix and testOthers:
    class UnixTest(CreateConnectionsTest):
        ListenerClass = Listener.UnixListener

if Listener.has_ipv6 and testOthers:
    class Ipv6Test(CreateConnectionsTest):
        ListenerClass = Listener.IPv6Listener

    def test_listeners_address_is_colonColon1(self):
        self.assertEquals(self.listener.listener.address[0], '::1')
        

class IPv4Test(CreateConnectionsTest):

    def test_listeners_address_is_0000(self):
        self.assertEquals(self.listener.listener.address[0], '0.0.0.0')

class IPv4Test1(unittest.TestCase):

    port = 2345
    def setUp(self):
        self.port += 1
        self.address = ('127.0.0.1', self.port)
        self.listener = Listener.IPv4Listener(self.address)
        self.listener.listen()

    def test_getAddress(self):
        p = self.listener.getConnectionPossibilities()
        function, args = p[0]
        self.assertIn(self.address, args)

    def test_socket_listens(self):
        import socket
        s = socket.socket()
        s.settimeout(3)
        s.connect(self.address)
        s.close()
        self.assertTrue(self.listener.isListening())
        

if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
