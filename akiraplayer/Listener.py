
import traceback
import thread
import socket
import os

from multiprocessing.connection import AuthenticationError, Client
from multiprocessing.connection import deliver_challenge, answer_challenge
from multiprocessing.connection import families as connection_families


has_ipv6 = socket.has_ipv6
has_unix = 'AF_UNIX' in connection_families
has_pipe = 'AF_PIPE' in connection_families

class ConnectionBroken(EOFError):
    pass

class NoProcess(object):
    @staticmethod
    def isProcess():
        return False

class BaseConnection(object):
    
    _connected = False
    _threadId = None
    _fromProcess = None
    _toProcess = None

    def listen(self):
        self.startListening()
        self._threadId = 'running'
        self._threadId = thread.start_new(self.listenForConnections, ())

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

    def call(self, aFunction, args, kw):
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

class BrokenConnection(BaseConnection):
    
    def call(*args):
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

    def getListenAddress(self):
        if self.family and self.family.startswith('AF_INET'):
            return ('', 0)
        return None

    def getListener(self):
        address = self.getListenAddress()
        return self.Listener(address, family = self.family,
                             authkey = self.authkey)

    def startListening(self):
        self.listener = self.getListener()

    def accept(self):
        try:
            connection = self.listener.accept()
            self.addConnection(ClientConnection(connection))
        except IOError:
            # do nothing: connection broken
            pass
        except AuthenticationError:
            traceback.print_exc()

    def stopListening(self):
        self.listener.close()

    @property
    def addresses(self):
        return [self.listener.address]

    def getConnectionPossibilities(self):
        return map(self.getConnectClient, self.addresses)

    def getConnectClient(self, address):
        return (connectClient, (address, self.family, self.authkey))
    
    def close(self):
        BaseConnection.close(self)
        self.listener.close()

    def addConnection(self, connection):
        pass

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

class IPv4Listener(IPListener):

    ALLADDRESSES = ['0.0.0.0']

    def __init__(self, address = ('', 0)):
        IPListener.__init__(self, address, 'AF_INET')

    @staticmethod
    def getHostNames():
        hostName, ipv6, ipv4 = socket.gethostbyname_ex(socket.gethostname())
        return ['localhost', hostName] + ipv4

if socket.has_ipv6:
    class IPv6Listener(IPListener):

        ALLADDRESSES = ['::']
        families = IPListener.families[:] + ['AF_INET6']

        def __init__(self, address = ('::', 0)):
            IPListener.__init__(self, address, 'AF_INET6')

        @staticmethod
        def getHostNames():
            hostName, ipv6, ipv4 = socket.gethostbyname_ex(socket.gethostname())
            return ['::1', hostName] + ipv6

        def getConnectClient(self, address):
            return (connectClientIPv6, (address, self.authkey))


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
            obj = self._connection.recv()
        except (EOFError, IOError):
            self.close()
        except:
            ## todo: send the error back to where it came from
            traceback.print_exc()
            
    def call(self, aFunction, args, kw):
        self.send(R(callFunction, aFunction, args, kw))



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
