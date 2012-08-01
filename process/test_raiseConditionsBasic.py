import sys
import unittest
import time
import socket
import pickle
import thread
import select

import traceback

import multiprocessing.connection

startedThreads = []
def thread_start_new(*args, **kw):
    id = thread.start_new(*args, **kw)
    startedThreads.append(id)
    return id

class X(object):
    @staticmethod
    def close():
        pass

TIMEOUT = 0.1

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
        self.lock = thread.allocate_lock()

    def acceptThread(self):
        while self.open:
            self.accepts_start += 1
            try:
                while 1:
                    with self.lock:
                        l = [self.listener._listener._socket.fileno()]
                        rd, wd, xx = select.select(l, l, l, 0)
                        if rd or xx or wd:
                            self.connection1 = self.listener.accept()
                            break
                    time.sleep(0.001)
            except socket.error:
                self.socketError = True
                break
            except:
                traceback.print_exc()
                break
            finally:
                self.accepts_end += 1
            time.sleep(TIMEOUT)

    def test_accepted_once(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        time.sleep(TIMEOUT)
        self.assertEquals(self.accepts_end, 1)

    def test_thread_is_closed(self):
        self.listener.close()
        time.sleep(TIMEOUT)
        self.assertEquals(self.accepts_end, 1)
        self.assertTrue(self.socketError)
        
    def test_thread_is_closed_after_connection(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        with self.lock:
            self.listener.close()
        for i in range(int(5 / TIMEOUT)):
            time.sleep(TIMEOUT)
            if self.accepts_end != 0:
                break
        self.assertEquals(self.accepts_end, 1)
        self.assertTrue(self.socketError)

    def test_thread_is_closed_after_connection_fast_close(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        time.sleep(TIMEOUT)
        self.assertEquals(self.accepts_end, 1)
        self.listener.close()
        time.sleep(TIMEOUT)
        self.assertEquals(self.accepts_end, 2)
        self.assertTrue(self.socketError)

    def test_close_allconnections_before_listener(self):
        self.connection2 = multiprocessing.connection.Client(self.listener.address)
        time.sleep(TIMEOUT)
        self.connection1.close()
        self.connection2.close()
        self.listener.close()
        time.sleep(TIMEOUT)
        self.assertEquals(self.accepts_end, 2)
        self.assertTrue(self.socketError)

    def tearDown(self):
        self.connection1.close()
        self.connection2.close()
        self.listener.close()
        self.open = False


if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
    time.sleep(TIMEOUT)
    if False:
        import sys
        time.sleep(2) # wait for threads to die
        print 'frames:', len(sys._current_frames().items())
        for k in sorted(sys._current_frames()):
            f = sys._current_frames()[k]
            
            if k in startedThreads:
                print f.f_code.co_filename,
                print k, f.f_code.co_firstlineno
                ## C:\Python27\lib\socket.py 8044 201 ## socket.accept
            else:
                print
        print 'frames:', len(sys._current_frames().items())
