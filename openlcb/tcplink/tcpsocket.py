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

    def settimeout(self, seconds):
        """Set the timeout for connect and transfer.

        Args:
            seconds (float): The number of seconds to wait before
                a timeout error occurs.
        """
        self.sock.settimeout(seconds)

    def connect(self, host, port):
        self.sock.connect((host, port))

    def send(self, data):
        '''Send a single message, provided as an [int]
        '''
        msg = bytes(data)
        total_sent = 0
        while total_sent < len(msg[total_sent:]):
            sent = self.sock.send(msg[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent = total_sent + sent

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

    def close(self):
        self.sock.close()
        return
