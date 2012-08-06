
from pickle import dumps, loads
from R import R

currentProcess = None
class MockProcess(object):
    '''this is a mock process
the context handlers make it the ThisProcess within'''

    proc = {}

    def __init__(self, name):
        self.proc.setdefault(name, self)
        self.name = name
        self.db = None
        self.local = False

    def isThisProcess(self):
        return self.local

    def call(self, *args):
##        print 'dump -->'
        s = dumps(R(args))
##        print '<-- dump'
        def g():
            with self.proc[self.name]:
                ## use the original process
##                print 'load -->'
                loads(s)
##                print '<-- load'
        self.without(g)
        

    def __enter__(self):
        global currentProcess
##        print 'enter', proc, self
        assert currentProcess is None or currentProcess is self
        currentProcess = self
        self.local = True

    def __reduce__(self):
        return loadProc, (self.name,)

    def __exit__(self, *args):
##        print 'exit', self
        self.local = False
        global currentProcess
        currentProcess = None

    def isMock(self): return True

    def without(self, func):
        _proc = currentProcess
        if _proc:_proc.__exit__()
        try:
            return func()
        finally:
            if _proc:_proc.__enter__()

    @classmethod
    def reset(cls):
        global currentProcess
        currentProcess = None
        cls.proc = {}

    def __repr__(self):
        return 'MP[%s]' % (self.name,)

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def current():
        return currentProcess


def loadProc(name):
    assert currentProcess is not None
    if name == currentProcess.name:
        return currentProcess
    l = currentProcess.MockInOtherProcess
    return currentProcess.without(lambda: l(name))

class MockInOtherProcess(MockProcess):
    def __repr__(self):
        return 'MIOP[%s]' % (self.name,)


MockProcess.MockInOtherProcess = MockInOtherProcess


__all__ = ['MockProcess', 'MockInOtherProcess']
