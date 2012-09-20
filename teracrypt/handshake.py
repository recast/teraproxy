import random
import itertools
import teracrypt.cipher


def get_random_bytes(bytes):
    return ''.join([chr(random.randrange(0, 256)) for x in xrange(bytes)])


def xor_string(left, right):
    return ''.join([chr(ord(a) ^ ord(b)) for a, b in itertools.izip(left, right)])


def shift_right(data, bytes):
    return data[-bytes:] + data[:-bytes]


def handshake(sock):
    KEY_BYTES = 128

    privateKey = get_random_bytes(KEY_BYTES)
    publicKey = get_random_bytes(KEY_BYTES)
    encryptCipher = teracrypt.cipher.Cipher(privateKey)

    sock.sendall(publicKey)

    fd = sock.makefile('rb')

    serverPublicKey = xor_string(shift_right(fd.read(KEY_BYTES), 31), publicKey)

    sock.sendall(shift_right(xor_string(serverPublicKey, privateKey), 17))

    serverPrivateKey = encryptCipher.cipher(shift_right(fd.read(KEY_BYTES), 79))
    decryptCipher = teracrypt.cipher.Cipher(serverPrivateKey)

    return encryptCipher, decryptCipher
