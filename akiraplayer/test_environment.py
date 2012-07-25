import socket
import multiprocessing.connection
import unittest
import thread
import time

socket.setdefaulttimeout(1)

class SocketTest(unittest.TestCase):

    def test_accepting_socket_stops_when_closed(self):
        s = socket.socket()
        s.bind(('', 0))
        s.listen(1)
        l = []
        def g():
            try:
                l.append(s.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        s.close()
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])
        
    def test_accepting_socket_stops_when_closed_and_reuse_addr(self):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 0))
        s.listen(1)
        l = []
        def g():
            try:
                l.append(s.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        time.sleep(1)
        s.close()
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])
        
    def test_accepting_socket_stops_when_closed_after_accepting_once(self):
        s = socket.socket()
        s.bind(('', 0))
        s.listen(1)
        l = []
        def g():
            try:
                x = s.accept()
                l.append(s.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        s2 = socket.socket()
        s2.connect(('localhost', s.getsockname()[1]))
        s2.close()
        time.sleep(1)
        s.close()
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])
    def test_accepting_socket_stops_when_closed_after_accepting_once2(self):
        s = socket.socket()
        s.bind(('', 0))
        s.listen(1)
        l = []
        def g():
            try:
                x = s.accept()
                time.sleep(1)
                l.append(s.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        s2 = socket.socket()
        s2.connect(('localhost', s.getsockname()[1]))
        s2.close()
        s.close()
        time.sleep(1)
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])

class SocketListenerTest(unittest.TestCase):

    def test_accepting_socket_stops_when_closed(self):
        li = multiprocessing.connection.SocketListener(('', 0), 'AF_INET')
        l = []
        def g():
            try:
                l.append(li.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        time.sleep(1)
        li.close()
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])
 
    def test_accepting_socket_stops_when_closed_after_accepting_once(self):
        li = multiprocessing.connection.SocketListener(('', 0), 'AF_INET')
        l = []
        def g():
            try:
                x = li.accept()
                l.append(li.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        s2 = socket.socket()
        s2.connect(('localhost', li._address[1]))
        s2.close()
        time.sleep(1)
        li.close()
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])

    def test_accepting_socket_stops_when_closed_after_accepting_once2(self):
        li = multiprocessing.connection.SocketListener(('', 0), 'AF_INET')
        l = []
        def g():
            try:
                x = li.accept()
                time.sleep(1)
                l.append(li.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        s2 = socket.socket()
        s2.connect(('localhost', li._address[1]))
        
        li.close()
        time.sleep(1)
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])
        s2.close()
 
if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
