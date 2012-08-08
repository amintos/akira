import Process
import thread

def pyGet(obj = Process.thisProcess):
    import pickle
    s = pickle.dumps(obj)
    l = []
    while s:
        l.append(s[:40])
        s = s[40:]
    s = map(repr, l)
    s = '\\\n'.join(s)
    return '__import__("pickle").loads(\\\n%s)' % s

def pyPrint(obj = Process.thisProcess):
    print 'o = %s' % pyGet(obj)

running = thread.allocate_lock()
    
def run():
    pyPrint()
    running.acquire(False)
    running.acquire()
    running.release()

def stop():
    running.release()

if __name__ == '__main__':
    Process.thisProcess.listenWhereYouCan()
    try:from tools import *
    except ImportError:pass
    import sys
    if not 'idlelib' in sys.modules:
        run()
