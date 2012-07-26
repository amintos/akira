import sys
import unittest
import time
import socket
import pickle
import thread

import traceback

import Listener

from Listener import ConnectionPossibility

import multiprocessing.connection

startedThreads = []
def thread_start_new(*args, **kw):
    id = thread.start_new(*args, **kw)
    startedThreads.append(id)
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

TIMEOUT = 0.01

class CreateConnectionsTestIpv4(unittest.TestCase):

    ListenerClass = Listener.IPv4Listener

    def setUp(self):
        global value
        value = 'valueNotSet'
        self.listener = self.ListenerClass()
        self.listener.fromProcess(SomeProcess)
        self.listener.listen()
        self.accepts_started = 0
        self.accepts_ended = 0
        self._connections = []
        self._accept = self.listener.listener._listener.accept
        self.listener.listener._listener.accept = self.accept

    def accept(self):
        self.accepts_started += 1
        try:
            conn = self._accept()
            return conn
        finally:
            self.accepts_ended += 1
    
    def getConnection(self):
        conn = self.listener.getConnectionPossibilities()[0]()
        self._connections.append(conn)
        return conn
    
    def test_create_connection_success(self):
        connection = self.getConnection()
        time.sleep(TIMEOUT)
        SomeProcess._connections.pop().close()
        connection.close()
        self.listener.close()
        time.sleep(TIMEOUT)
        self.assertEquals(self.accepts_started, self.accepts_ended)
        time.sleep(TIMEOUT)

    def test_create_connection_closed_patched(self):
        close_called = []
        def close():
            close_called.append(1)
            return _close()
        _close = self.listener.listener._listener.close
        self.listener.listener._listener.close = close
        connection = self.getConnection()
        time.sleep(TIMEOUT)
        SomeProcess._connections.pop().close()
        connection.close()
        self.listener.close()
        time.sleep(TIMEOUT)
        self.assertNotEquals(close_called, [])

    def test_create_connection_success2(self):
        connection = self.getConnection()
        connection.close()
        self.listener.close()
        time.sleep(TIMEOUT)
        SomeProcess._connections.pop().close()
        self.assertEquals(self.accepts_started, self.accepts_ended)
        time.sleep(TIMEOUT)

    def tearDown(self):
        self.listener.close()
        for conn in self._connections + SomeProcess._connections:
            conn.close()


if Listener.has_ipv6:
    class CreateConnectionsTestIpv6(CreateConnectionsTestIpv4):
        ListenerClass = Listener.IPv6Listener

if Listener.has_pipe:
    class CreateConnectionsTestPipe(CreateConnectionsTestIpv4):
        ListenerClass = Listener.PipeListener

if Listener.has_unix:
    class CreateConnectionsTestUnix(CreateConnectionsTestIpv4):
        ListenerClass = Listener.UnixListener


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
