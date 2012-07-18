import socket
from BenchmarkPipe import testTroughput

if __name__ == '__main__':
    s = socket.socket()
    s.bind(('localhost', 0))
    s.listen(1)
    s1 = socket.socket()
    s1.connect(('localhost', s.getsockname()[1]))
    s2, addr = s.accept()
    
    testTroughput(s2.recv,
                  s1.send,
                  'Benchmark of socket.socket.send')

    
