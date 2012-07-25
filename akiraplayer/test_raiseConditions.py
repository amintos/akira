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

class X(object):
    @staticmethod
    def close():
        pass

class CreateConnectionsPrimitiveTest(unittest.TestCase):

    def setUp(self):
        self.connection1 = X
        self.connection2 = X
        self.listener = multiprocessing.connection.Listener(('127.0.0.1', 0), 'AF_INET')
        self.open = True
        self.accepts_start = 0
        self.accepts_end = 0
        self.socketError = False
        thread_start_new(self.acceptThread, ())

    def acceptThread(self):
        while self.open:
            self.accepts_start += 1
            try:
                self.connection1 = self.listener.accept()
            except socket.error:
                self.socketError = True
                break
            except:
                traceback.print_exc()
                break
            finally:
                self.accepts_end += 1
            time.sleep(0.1)

    def test_accepted_once(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        time.sleep(1)
        self.assertEquals(self.accepts_end, 1)

    def test_thread_is_closed(self):
        self.listener.close()
        time.sleep(1)
        self.assertEquals(self.accepts_end, 1)
        self.assertTrue(self.socketError)
        
    def test_thread_is_closed_after_connection(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        self.listener.close()
        time.sleep(1)
        self.assertEquals(self.accepts_end, 2)
        self.assertTrue(self.socketError)

    def test_thread_is_closed_after_connection_fast_close(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        time.sleep(1)
        self.listener.close()
        self.assertEquals(self.accepts_end, 2)
        self.assertTrue(self.socketError)

    def test_close_allconnections_before_listener(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        time.sleep(1)
        self.connection1.close()
        self.connection2.close()
        self.listener.close()
        self.assertEquals(self.accepts_end, 2)
        self.assertTrue(self.socketError)

    def tearDown(self):
        self.connection1.close()
        self.connection2.close()
        self.listener.close()
        self.open = False

class CreateConnectionsTest(object):#unittest.TestCase):

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
            return self._accept()
        finally:
            self.accepts_ended += 1
    
    def getConnection(self):
        conn = self.listener.getConnectionPossibilities()[0]()
        self._connections.append(conn)
        return conn
    
    def test_create_connection_success(self):
        connection = self.getConnection()
        time.sleep(1)
        SomeProcess._connections[0].close()
        connection.close()
        self.listener.close()
        time.sleep(1)
        self.assertEquals(self.accepts_started, self.accepts_ended)
        time.sleep(1)

    def test_create_connection_closed_patched(self):
        close_called = []
        def close():
            close_called.append(1)
            return _close()
        _close = self.listener.listener._listener.close
        self.listener.listener._listener.close = close
        connection = self.getConnection()
        time.sleep(1)
        SomeProcess._connections[0].close()
        connection.close()
        self.listener.close()
        time.sleep(1)
        self.assertEquals(close_called, [1])
        time.sleep(1)

    def test_create_connection_success2(self):
        connection = self.getConnection()
        SomeProcess._connections[0].close()
        connection.close()
        self.listener.close()
        time.sleep(1)
        self.assertEquals(self.accepts_started, self.accepts_ended)
        time.sleep(1)

##    def test_send_command_through_connection(self):
##        connection = self.getConnection()
##        thread.start_new(connection.call, (setValue, ('valueSet',), {}))
##        i = 0
##        for i in range(100):
##            if value == 'valueSet':
##                break
##            time.sleep(0.001)
##        self.assertEquals(value, 'valueSet')

    def tearDown(self):
        self.listener.close()
        for conn in self._connections + SomeProcess._connections:
            conn.close()


if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 2)
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
