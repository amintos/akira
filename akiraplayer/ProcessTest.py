import unittest
import Process
import os
import time
import socket
import pickle

from Process import thisProcess

value = None

def setValue(aValue):
    global value
    value = aValue


class MockListener1(object):
    
    listening = False
    def listen(self):
        self.listening = True

    closed = False
    def close(self):
        self.closed = True

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
        self.assertIs(pickle.loads(pickle.dumps(thisProcess)), thisProcess)

    def test_added_listener_will_listen(self):
        listener = MockListener1()
        self.assertFalse(listener.listening)
        thisProcess.addListener(listener)
        self.assertTrue(listener.listening)
        thisProcess.removeListener(listener)
        self.assertTrue(listener.closed)


if __name__ == '__main__':
    unittest.main(exit = False)
