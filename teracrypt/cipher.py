import itertools
import struct
import teracrypt.sha


class CipherComponent(object):

    def __init__(self, key, pos2):
        self.key = struct.unpack('=%dI' % (len(key) / 4), key)
        self.overflow = False
        self.value = 0
        self.pos1 = 0
        self.pos2 = pos2

    def next(self):
        p1 = self.key[self.pos1]
        p2 = self.key[self.pos2]
        min = p1
        if p2 <= p1:
            min = p2
        self.value = (p1 + p2) & 0xFFFFFFFF

        self.pos1 += 1
        self.pos2 += 1
        self.overflow = min > self.value
        if self.pos1 == len(self.key):
            self.pos1 = 0
        if self.pos2 == len(self.key):
            self.pos2 = 0


class Cipher(object):

    def __init__(self, key):
        KEY_BYTES = 680

        keyLenByte = chr(len(key) & 0xFF)
        key = (key * ((KEY_BYTES / len(key)) + 1))[:KEY_BYTES]
        key = keyLenByte + key[1:]

        i = 0
        while i < len(key):
            hash = teracrypt.sha.sha()
            hash.update(key)
            digest = hash.digest()

            key = key[:i] + digest + key[i + len(digest):]

            i += len(digest)

        self.sub1 = CipherComponent(key[:55 * 4], 31)
        self.sub2 = CipherComponent(key[55 * 4:(55 + 57) * 4], 50)
        self.sub3 = CipherComponent(key[(55 + 57) * 4:], 39)
        self.keystream = []

    def more(self):
        flag = self.sub1.overflow & self.sub2.overflow | self.sub3.overflow & (self.sub1.overflow | self.sub2.overflow)

        if self.sub1.overflow == flag:
            self.sub1.next()

        if self.sub2.overflow == flag:
            self.sub2.next()

        if self.sub3.overflow == flag:
            self.sub3.next()

        value = self.sub1.value ^ self.sub2.value ^ self.sub3.value
        self.keystream.extend([ord(x) for x in struct.pack('=I', value)])

    def cipher(self, data):
        while len(data) > len(self.keystream):
            self.more()

        data = ''.join([chr(ord(a) ^ b) for a, b in itertools.izip(data, self.keystream[:len(data)])])
        self.keystream = self.keystream[len(data):]
        return data
