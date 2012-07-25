from threading import local
from Queue import Empty

class ConnectionStack(local):
    ''' this stack stacks all connections currently running in a thread.
use like this

    with runningConnection(connection):
        assert runningConnection.top() is connection
'''

    def __init__(self):
        self.connectionStack = []

    def __call__(self, aConnection):
        return TemporaryStackElement(self, aConnection)


    def push(self, anElement):
        self.connectionStack.append(anElement)

    def pop(self):
        return self.connectionStack.pop()

    def top(self):
        if self.isEmpty():
            raise Empty('No connections on stack.')
        return self.connectionStack[-1]

    def isEmpty(self):
        return not self.connectionStack

class topConnection(ConnectionStack):
    def __reduce__(self):
        return self.__class__.__name__

topConnection = topConnection()

_nix = []
def top(default = _nix):
    '''return the uppermost connection of the stack
if default is given default will be returned if no top'''
    if default == _nix:
        return topConnection.top()
    elif topConnection.isEmpty():
        return default
    return topConnection.top()
