'''
simple serial nput for string send and receive
expects prior setting of device name
'''
import serial

MSGLEN = 35

class SerialLink:
    def __init__(self):
        pass
        
    def connect(self, device, baudrate=230400):
        self.port = serial.Serial(device, baudrate)

    # send a single string
    def send(self, string):
        msg = string.encode('ascii')
        totalsent = 0
        while totalsent < len(msg[totalsent:]):
            sent = self.port.write(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        '''Receive at least one GridConnect frame and return as string.
        - Guarantee: If input is valid, there will be at least one ";" in the
          response.
        - This makes it nicer to display the raw data.
        - Note that the response may end with a partial frame.
        '''
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.port.read(1)
            if chunk == b'':
                raise RuntimeError("serial connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
            if 0x3B in chunk:
                break
        return b''.join(chunks).decode("utf-8")
