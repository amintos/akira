import socket
import multiprocessing.connection
import unittest
import thread
import time
import select

socket.setdefaulttimeout(1)

TIMEOUT = 0.01

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
        time.sleep(TIMEOUT)
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
        time.sleep(TIMEOUT)
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
                time.sleep(TIMEOUT)
                l.append(s.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        s2 = socket.socket()
        s2.connect(('localhost', s.getsockname()[1]))
        s2.close()
        s.close()
        time.sleep(TIMEOUT)
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])

    def test_closed_socket_cannot_select_to_accept(self):
        s = socket.socket()
        s.bind(('', 0))
        s.listen(1)
        rf = [s.fileno()] * 1
        wf = [s.fileno()] * 1
        xf = [s.fileno()] * 1
        s.close()
        t = -time.time()
        try:
            lr, lw, lx = select.select(rf, wf, xf, TIMEOUT)
        except select.error:
            pass
        else:
            t += time.time()
            self.assertLess(t, TIMEOUT)
            
    def test_open_socket_can_select_to_accept(self):
        s = socket.socket()
        s.bind(('', 0))
        s.listen(1)
        rf = [s.fileno()] * 1
        wf = [s.fileno()] * 1
        xf = [s.fileno()] * 1
        t = -time.time()
        try:
            lr, lw, lx = select.select(rf, wf, xf, TIMEOUT)
        except select.error:
            self.fail()
        else:
            t += time.time()
            self.assertGreater(t, TIMEOUT)
        
    def test_close_between__select_and_accept(self):
        s = socket.socket()
        s.bind(('', 0))
        s.listen(1)
        s1 = socket.socket()
        s1.connect(('localhost', s.getsockname()[1]))
        rf = [s.fileno()] * 1
        wf = [s.fileno()] * 1
        xf = [s.fileno()] * 1
        t = -time.time()
        try:
            lr, lw, lx = select.select(rf, wf, xf, TIMEOUT)
        except select.error:
            self.fail()
        else:
            t += time.time()
            self.assertLess(t, TIMEOUT)
            s.close()
            self.assertRaises(socket.error, s.accept)
        

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
        time.sleep(TIMEOUT)
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
        time.sleep(TIMEOUT)
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
                time.sleep(TIMEOUT)
                l.append(li.accept())
            except socket.error:
                l.append(2)
        thread.start_new(g, ())
        s2 = socket.socket()
        s2.connect(('localhost', li._address[1]))
        
        li.close()
        time.sleep(TIMEOUT)
        for i in range(100):
            time.sleep(0.001)
            if l:
                break
        self.assertEquals(l, [2])
        s2.close()
 
if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
