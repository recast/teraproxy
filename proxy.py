import struct
import traceback

import gevent
import gevent.server
import gevent.backdoor
from gevent import socket

import handler
import teracrypt.handshake


remote_addr = None
proxies = []


class Proxy(object):

    def __init__(self, client_sock, server_sock, encrypt_cipher, decrypt_cipher):
        global proxies

        self.client_sock = client_sock
        self.server_sock = server_sock
        self.encrypt_cipher = encrypt_cipher
        self.decrypt_cipher = decrypt_cipher
        proxies.append(self)

    def handle_socket(self, server):
        if server:
            sock = self.server_sock
            remote_sock = self.client_sock
            cipher = self.decrypt_cipher
        else:
            sock = self.client_sock
            remote_sock = self.server_sock
            cipher = None

        fd = sock.makefile('rb')
        while True:
            data = self.read_message(fd, cipher)
            if not data:
                break

            try:
                if handler.want_reload():
                    reload(handler)
                handler.handle_message(self, server, data)
            except:
                traceback.print_exc()

        remote_sock.shutdown(socket.SHUT_RDWR)
        remote_sock.close()

    def read(self, fd, length, cipher=None):
        data = fd.read(length)
        if cipher and data:
            data = cipher.cipher(data)
        return data

    def read_message(self, fd, cipher=None):
        length_data = self.read(fd, 2, cipher)
        if not length_data:
            return None

        length, = struct.unpack('=H', length_data)
        data = self.read(fd, length - 2, cipher)
        if not data:
            return None

        return length_data + data

    def write(self, server, data):
        sock = self.server_sock if server else self.client_sock
        if server:
            data = self.encrypt_cipher.cipher(data)

        sock.sendall(data)


def handle_connection(client_sock, client_addr):
    global remote_addr

    print 'connection from', client_addr

    server_sock = socket.create_connection(remote_addr)
    server_fd = server_sock.makefile('rb')
    assert(server_fd.read(4) == '\x01\x00\x00\x00')

    encryptCipher, decryptCipher = teracrypt.handshake.handshake(server_sock)

    client_sock.sendall('\x00\x00\x00\x00')
    proxy = Proxy(client_sock, server_sock, encryptCipher, decryptCipher)
    gevent.spawn(proxy.handle_socket, False)
    gevent.spawn(proxy.handle_socket, True)


def main():
    from sys import argv
    global remote_addr

    local_address, local_port, remote_address, remote_port, backdoor_address, backdoor_port = argv[1:]
    remote_addr = (remote_address, int(remote_port))

    backdoor = gevent.backdoor.BackdoorServer((backdoor_address, int(backdoor_port)), locals=globals())
    backdoor.start()

    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((local_address, int(local_port)))
    listener.listen(50)

    server = gevent.server.StreamServer(listener, handle_connection)
    server.serve_forever()


if __name__ == '__main__':
    main()
