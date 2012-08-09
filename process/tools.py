import Process
import thread

def pyGet(obj = Process.thisProcess):
    import pickle
    s = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    s = s.encode('base64')
    return '__import__("pickle").loads("""\n%s""".decode("base64"))' % s

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
