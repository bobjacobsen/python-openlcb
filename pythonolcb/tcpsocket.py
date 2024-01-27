# simple TCP socket input for string send and receive
# expects prior setting of host and port variables

# https://docs.python.org/3/howto/sockets.html
import socket
MSGLEN = 35 # longest GC frame is 31 letters, so forward if getting non-GC input
class TcpSocket:

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    # send a single string
    def send(self, string):
        msg = string.encode('ascii')
        totalsent = 0
        while totalsent < len(msg[totalsent:]) :
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    # receive at least one GridConnect frame and return as string.
    # Guarantee: If input is valid, there will be at least one ";" in the response.  
    # This makes it nicer to display the raw data.
    # Note that the response may end with a partial frame.
    def receive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 1))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
            if 0x3B in chunk : break
        return b''.join(chunks).decode("utf-8") 

