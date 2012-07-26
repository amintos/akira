
import traceback
import thread
import socket
import time
import os

from thread import start_new as thread_start_new

from multiprocessing.connection import AuthenticationError, Client
from multiprocessing.connection import deliver_challenge, answer_challenge
from multiprocessing.connection import families as connection_families

from TopConnection import topConnection
import TopConnection

import select

pipes_are_supported = False
has_ipv4 = hasattr(socket, 'AF_INET')
has_ipv6 = socket.has_ipv6
has_unix = 'AF_UNIX' in connection_families
has_pipe = 'AF_PIPE' in connection_families and pipes_are_supported

class ConnectionMustBeTop(Exception):
    '''The connection must be the top connection

do something like this:
with connection:
    # here is where the error now does not occur
    ...

'''

class ConnectionBroken(EOFError):
    pass

class NoProcess(object):
    @staticmethod
    def isProcess():
        return False

    def acceptedConnection(self, connection):
        pass

    def __nonzero__(self):
        return False

class BaseConnection(object):
    
    _connected = False
    _threadId = None
    _fromProcess = NoProcess()
    _toProcess = NoProcess()

    def listen(self):
        self.startListening()
        self._threadId = 'running'
        self._threadId = thread_start_new(self.listenForConnections, ())

    def isListening(self):
        return self._threadId is not None

    def listenForConnections(self):
        thread_id = thread.get_ident()
        try:
            while self._threadId == 'running':
                self.accept()
            while self._threadId == thread_id:
                self.accept()
        finally:
            self.stopListening()

    def startListening(self):
        pass

    def stopListening(self):
        pass

    def isConnected(self):
        return self._connected

    def call(self, aFunction, args, kw = {}):
        raise NotImplementedError('todo')

    def close(self):
        self._threadId = None

    def getConnectionPossibilities(self):
        return []

    def accept(self):
        raise NotImplementedError('to be implemented in subclasses')

    def fromProcess(self, process = NoProcess):
        if process.isProcess():
            self._fromProcess = process
        return self._fromProcess

    def toProcess(self, process = NoProcess):
        if process.isProcess():
            self._toProcess = process
        return self._toProcess

    def __str__(self):
        s = '%s' % type(self).__name__
        if self.fromProcess():
            s += ' from %s' % (self.fromProcess(),)
        if self.toProcess():
            s += ' to %s' % (self.toProcess(),)

    def __enter__(self):
        topConnection.push(self)

    def __exit__(self, *args):
        assert topConnection.pop() is self, 'Connection stack should be consistent.'
            
    def __reduce__(self):
        if TopConnection.top(None) != self:
            raise ConnectionMustBeTop('to be serialized.')
        return TopConnection.top, ()

class ConnectionPossibility(object):
    def __init__(self, function, args = (), kw = {}):
        self.function = function
        self.args = args
        self.kw = kw

    def __reduce__(self):
        return self.__class__, (self.function, self.args, self.kw)

    def __call__(self):
        return self.function(*self.args, **self.kw)

    def __eq__(self, other):
        if other.__class__ is object:
            return False
        if issubclass(self.__class__, other.__class__):
            return self.function == other.function and \
                   self.args == other.args and \
                   self.kw == other.kw
        if issubclass(other.__class__, self.__class__):
            return other == self
        return False
        


class BrokenConnection(BaseConnection):
    
    def call(*args, **kw):
        raise ConnectionBroken('this connection was never and is no more')

    def accept(self):
        raise ConnectionBroken('this connection was never and is no more')

    def listen(self):
        pass

CHALLENGELENGTH = 20

class Listener(BaseConnection):

    from multiprocessing.connection import Listener as Listener

    families = connection_families[:]

    def __init__(self, family = None):
        if family is not None:
            assert family in self.families, \
                'family %r must be one of %r' % (family, self.families)
        self.family = family
        self.authkey = os.urandom(CHALLENGELENGTH)
        self.listener = None

    def getListenAddress(self):
        if self.family and self.family.startswith('AF_INET'):
            return ('', 0)
        return None

    def getListener(self):
        address = self.getListenAddress()
        return self.Listener(address, family = self.family,
                             authkey = self.authkey)

    def startListening(self):
        assert self.listener is None
        self.listener = self.getListener()

    def accept(self):
        try:
            with self:
                connection = self.acceptConnection()
        except IOError:
            ## connection broken
            pass
        else:
            clientConnection = ClientConnection(connection)
            self.acceptedConnection(clientConnection)

    def acceptConnection(self):
        raise NotImplementedError('this must be implemented in subclasses')

    def stopListening(self):
        self.listener.close()

    @property
    def addresses(self):
        return [self.listener.address]

    def getConnectionPossibilities(self):
        return map(self.getConnectClient, self.addresses)

    def getConnectClient(self, address):
        return ConnectionPossibility(connectClient,
                                     (address, self.family, self.authkey))
    
    def close(self):
        BaseConnection.close(self)
        self.listener.close()
        
    def acceptedConnection(self, connection):
        self.fromProcess().acceptedConnection(connection)

def connectClient(*args):
    return ClientConnection(Client(*args))

if has_unix:
    class UnixListener(Listener):
        pass

class IPListener(Listener):

    ALLADDRESSES = []

    def __init__(self, address, family):
        Listener.__init__(self, family)
        self.__address = address
        self.lock = thread.allocate_lock()

    def getListenAddress(self):
        return self.__address

    @property
    def addresses(self):
        address = self.listener.address
        if address[0] in self.ALLADDRESSES:
            port = address[1]
            return [(hostName, port) for hostName in self.getHostNames()]
        return [address]

    @staticmethod
    def getHostNames():
        raise NotImplementedError('to implement in subclasses')

    def acceptConnection(self):
        while 1:
            with self.lock:
                ## todo: I do not understand why a lock should make it more
                ## threadsave. but it does.
                l = [self.fileno()]
                rd, wd, xx = select.select(l, l, l, 0)
                if rd or wd or xx:
                    return self.listener.accept()
            time.sleep(0.001)

    def fileno(self):
         return self.listener._listener._socket.fileno()

    def close(self):
        with self.lock:
            Listener.close(self)


def removeDuplicates(aList):
    noDuplicates = []
    for element in aList:
        if not element in noDuplicates:
            noDuplicates.append(element)
    return noDuplicates

class IPv4Listener(IPListener):

    ALLADDRESSES = ['0.0.0.0']

    def __init__(self, address = ('', 0)):
        IPListener.__init__(self, address, 'AF_INET')

    @staticmethod
    def getHostNames():
        hostName, ipv6, ipv4 = socket.gethostbyname_ex(socket.gethostname())
        return removeDuplicates(['127.0.0.1', hostName] + ipv4)

if socket.has_ipv6:
    class IPv6Listener(IPListener):

        ALLADDRESSES = ['::']
        families = IPListener.families[:] + ['AF_INET6']

        def __init__(self, address = ('::', 0)):
            IPListener.__init__(self, address, 'AF_INET6')

        @staticmethod
        def getHostNames():
            hostName, ipv6, ipv4 = socket.gethostbyname_ex(socket.gethostname())
            return removeDuplicates(['::1', hostName] + ipv6)

        def getConnectClient(self, address):
            return ConnectionPossibility(connectClientIPv6,
                                         (address, self.authkey))


    ## copied and adapted from multiprocessing.connection
    ## this can be removed when ipv6 support is built in in multiprocessing
    def SocketClientv6(address, authkey):
        '''
        Return a connection object connected to the socket given by `address`
        '''
        import _multiprocessing
        import errno
        import time
        from multiprocessing.connection import duplicate, _init_timeout
        from multiprocessing.connection import _check_timeout, debug
        s = socket.socket( socket.AF_INET6 )
        t = _init_timeout()

        while 1:
            try:
                s.connect(address)
            except socket.error, e:
                if e.args[0] != errno.ECONNREFUSED or _check_timeout(t):
                    debug('failed to connect to address %s', address)
                    raise
                time.sleep(0.01)
            else:
                break
        else:
            raise

        fd = duplicate(s.fileno())
        conn = _multiprocessing.Connection(fd)
        s.close()
        ## authenticate
        answer_challenge(conn, authkey)
        deliver_challenge(conn, authkey)
        return conn
    ## end of copy

    def connectClientIPv6(address, authkey):
        return ClientConnection(SocketClientv6(address, authkey))

else:
    def connectClientIPv6(*args):
        return BrokenConnection()

if has_pipe:
    class PipeListener(Listener):
        def __init__(self):
            Listener.__init__(self, 'AF_PIPE')
            self.lock = thread.allocate_lock()

        def acceptConnection(self):
##            raise IOError()
##            with self.lock:
                return self.listener.accept()

        def close(self):
##            with self.lock:
                Listener.close(self)

class R(object):
    def __init__(self, f, *args):
        self.ret = (f, args)
    def __reduce__(self):
        return self.ret
    def __call__(self, *args):
        raise NotImplementedError('never to be called')

def callFunction(aFunction, args, kw):
    return aFunction(*args, **kw)

class ClientConnection(BaseConnection):

    def __init__(self, connection):
        self._connection = connection
        self.send = connection.send
        self.recv = connection.recv
        self.fileno = connection.fileno
        self.listen()

    def accept(self):
        try:
            with self:
                obj = self._connection.recv()
        except (EOFError, IOError):
            self.close()
        except:
            ## todo: send the error back to where it came from
            traceback.print_exc()
            
    def call(self, aFunction, args, kw = {}):
        with self:
            self.send(R(callFunction, aFunction, args, kw))

    def close(self):
        BaseConnection.close(self)
        self._connection.close()



__all__ = ['ConnectionBroken', 'has_unix', 'has_ipv6', 'ClientConnection',
           'BaseConnection', 'BrokenConnection', 'IPv4Listener', 'R',
           'has_pipe'
           ]
if has_unix:
    __all__.append('UnixListener')
if has_ipv6:
    __all__.append('IPv6Listener')
if has_pipe:
    __all__.append('PipeListener')
