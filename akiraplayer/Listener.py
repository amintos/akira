
import traceback
import thread
import socket
import os

from multiprocessing.connection import AuthenticationError, Client
from multiprocessing.connection import families as connection_families

class BaseConnection(object):
    
    _connected = False
    _threadId = None

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

CHALLENGELENGTH = 20

class Listener(BaseConnection):

    from multiprocessing.connection import Listener as Listener

    families = connection_families[:]
    if socket.has_ipv6:
        families.append('AF_INET6')

    def __init__(self, family = None):
        self.family = family
        self.authkey = os.urandom(CHALLENGELENGTH)

    def getAddress(self):
        if self.family and self.family.startswith('AF_INET'):
            return ('', 0)
        return None

    def getListener(self):
        address = self.getAddress()
        return self.Listener(address, family = self.family,
                             authkey = self.authkey)

    def startListening(self):
        self.listener = self.getListener()

    def accept(self):
        try:
            connection = self.listener.accept()
            self.addConnection(ClientConnection(connection))
        except AuthenticationError:
            traceback.print_exc()

    def stopListening(self):
        self.listener.close()

    @property
    def addresses(self):
        address = self.listener.address
        if type(address) is tuple and address[:1] == ('0.0.0.0',):
            rest = address[1:]
            return [(hostName,) + rest for hostName in self.getHostNames()]
        return [address]

    def getConnectionPossibilities(self):
        return [(connectClient, (address, self.family, self.authkey))
                for address in self.addresses]

    @staticmethod
    def getHostNames():
        hostName, ipv6, ipv4 = socket.gethostbyname_ex(socket.gethostname())
        return ['localhost', '::1', hostName] + ipv6 + ipv4

    def close(self):
        BaseConnection.close(self)
        self.listener.close()

    def addConnection(self, connection):
        pass

def connectClient(*args):
    # todo: add ipv6 support
    return ClientConnection(Client(*args))

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
