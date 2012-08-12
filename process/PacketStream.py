import hmac as _hmac
import hashlib
import StringIO

class Cache(object):

    def __init__(self):
        self._cache = []
        self._filled = 0

    def cache(self, string):
        self._cache.append(string)
        self._filled += len(string)
    
    def readTo(self, callback, size):
        cache = self._cache
        s = ''
        while cache:
            s += cache.pop(0)
            if len(s) >= size:
                break
        if len(s) > size:
            cache.insert(0, s[size:])
            packet = s[:size]
        else:
            packet = s
        cache.insert(0, packet)
        callback(packet)
        self._filled -= len(cache.pop(0))

    def read(self, size):
        l = []
        self.readTo(l.append, size)
        return l[0]

    @property
    def size(self):
        return self._filled


class PacketWriter(object):
    '''This is a writer that splits the write input into packets of same size
and writes them to the function passed to it.
flush()
    can be used to make sure the last bytes do not remain in this writer
    but are written to the function passed to this object

if an error occurs no data is lost but will be written next time
write or flush is called.
'''


    def __init__(self, write, packetSize):
        self._cache = Cache()
        self._write = write
        self.packetSize = packetSize
        
    def write(self, string):
        self._cache.cache(string)
        while self._cache.size >= self.packetSize:
            self._writePacket()

    def _writePacket(self):
        self._cache.readTo(self._write, self.packetSize)


    def flush(self):
        while self._cache.size:
            self._writePacket()



class Secret(object):

    def __init__(self, string):
        self._string = string
        self.hmacLength = len(self.hmac(''))

    @property
    def signatureLength(self):
        return self.hmacLength

    @property
    def string(self):
        return self._string

    def hmac(self, string):
        return _hmac.new(self._string, string, hashlib.sha256).digest()

    def sign(self, string):
        return self.hmac(string) + string

    def signaturePart(self, string):
        return string[:self.hmacLength]
        
    def signedPart(self, string):
        return string[self.hmacLength:]

    def isSigned(self, string):
        return self.hmac(self.signedPart(string)) == self.signaturePart(string)


class HmacStream(object):

    def __init__(self, nextStream, secret):
        self._secret = secret
        self._nextStream = nextStream
        self._readCache = Cache()
        startSignature = secret.signaturePart(secret.sign(''))
        self._write_preceedingSignature = startSignature
        self._read_preceedingSignature = startSignature
        self._cachedPackets = {}

    def write(self, string):
        secret = self._secret
        assert len(self._write_preceedingSignature) ==secret.signatureLength
        message = self._write_preceedingSignature + string
        signedPacket = secret.sign(message)
        self._nextStream.write(signedPacket)
        self._write_preceedingSignature = secret.signaturePart(signedPacket)

    def read(self, size):
        while self._readCache.size < size:
            self._pullPacket()
            self._writePacketsToCache()
        return self._readCache.read(size)

    def _pullPacket(self):
        s = self._nextStream.readPacket()
        if self._secret.isSigned(s):
            secret = self._secret
            signature = self._secret.signaturePart(s)
            message = secret.signedPart(s)
            preceedingSignature = message[:secret.signatureLength]
            string = message[secret.signatureLength:]
            self._cachedPackets[preceedingSignature] = (signature, string)

    def _writePacketsToCache(self):
        while 1:
            message = self._cachedPackets.get(self._read_preceedingSignature)
            if message is None:
                break
            signature, string = message
            self._readCache.cache(string)
            self._read_preceedingSignature = signature
    
__all__ = ['PacketWriter', 'HmacStream', 'Secret', 'Cache']
