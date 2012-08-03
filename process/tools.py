import Process
import thread

def pyGet():
    import pickle
    s = pickle.dumps(Process.thisProcess)
    l = []
    while s:
        l.append(s[:50])
        s = s[40:]
    s = map(repr, l)
    s = '\\\n'.join(s)
    return '__import__("pickle").loads(\\\n%s)' % s

def pyPrint():
    print 'o = %s' % pyGet()

running = thread.allocate_lock()
    
def run():
    Process.thisProcess.listenWhereYouCan()
    pyPrint()
    running.acquire(False)
    running.acquire()
    running.release()

def stop():
    running.release()

if __name__ == '__main__':
    try:from tools import *
    except ImportError:pass
    import sys
    if not 'idlelib' in sys.modules:
        run()
