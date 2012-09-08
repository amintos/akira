
## not working

from socket import *
import time

def s(port):
    s3 = socket()
    s3.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s3.bind(('', port))
    return s3

def setting():
    return s1, s2, s3


def punch(other, port):
    s3 = s(port) # sock for making hole to outside
    s3.connect(('www.google.com', 80)) 
    s3.close()

    s1 = s(port)
    s1.listen(1) # sock for listening
    s1.setblocking(0)

    while 1:
        s2 = s(port) # sock for connecting
        s2.settimeout(1) 
        try:
            s2.connect(other)
            print 'success!'
            break
        except error as e:
            if e.args[0] == 10022:
                print 'e',
            else:
                print 'f',
        s2.close()
        try:
            sock, addr = s1.accept()
            print 'connect'
            break
        except error:
            pass
        time.sleep(0.01)
        
        


        
    
