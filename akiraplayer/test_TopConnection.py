
import thread
import unittest

from TopConnection import topConnection, top

import pickle

def dumpLoad(o):
    return pickle.loads(pickle.dumps(o))

class ConnectionStackTest(unittest.TestCase):

    def test_twoThreads(self):
        lock = thread.allocate_lock()
        topConnection.push(2)
        def x():
            try:
                self.assertTrue(topConnection.isEmpty())
                topConnection.push(1)
            finally:
                lock.release()
        lock.acquire()
        thread.start_new(x, ())
        self.assertEquals(topConnection.top(), 2)


    def test_pickle_top(self):
        self.assertEquals(dumpLoad(top), top)

    def test_pickle_topConnection(self):
        self.assertEquals(dumpLoad(topConnection), topConnection)

if __name__ == '__main__':
    unittest.main(exit = False)

    
