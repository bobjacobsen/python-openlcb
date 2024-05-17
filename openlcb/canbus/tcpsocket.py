'''
simple TCP socket input for string send and receive
expects prior setting of host and port variables
'''
# https://docs.python.org/3/howto/sockets.html
import socket
MSGLEN = 35  # longest GC frame is 31 letters; forward if getting non-GC input


class TcpSocket:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

    def send(self, string):
        """Send a single string.
        """
        msg = string.encode('ascii')
        totalsent = 0
        while totalsent < len(msg[totalsent:]):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        '''Receive at least one GridConnect frame and return as string.
        - Guarantee: If input is valid, there will be at least one ";" in the
          response.
        - This makes it nicer to display the raw data.
        - Note that the response may end with a partial frame.

        Returns:
            str: The received bytes decoded into a UTF-8 string.
        '''
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 1))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
            if 0x3B in chunk:
                break
        return b''.join(chunks).decode("utf-8")
