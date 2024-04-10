'''
simple TCP socket input for byte[] send and receive
expects prior setting of host and port variables
'''
# https://docs.python.org/3/howto/sockets.html
import socket


class TcpSocket:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            )
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def send(self, data):
        '''Send a single message, provided as an [int]
        '''
        msg = bytes(data)
        totalsent = 0
        while totalsent < len(msg[totalsent:]):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        '''Receive one or more bytes and return as an [int]
        Blocks until at least one byte is received, but may return more.

        Returns:
            list(int): one or more bytes, converted to a list of ints.
        '''
        chunk = self.sock.recv(128)
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        return list(chunk)  # convert from bytes
