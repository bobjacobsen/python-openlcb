# simple PySerial input for string send and receive
# expects prior setting of device and baudrate

# https://docs.python.org/3/howto/sockets.html
import serial

MSGLEN = 35 # longest GC frame is 31 letters, so forward if getting non-GC input
class SerialPort:

    def __init__(self, ser=None):
        self.ser = ser

    def connect(self, device, baudrate=230400):
        if self.ser is None :
            self.ser = serial.Serial()
            self.ser.port = device
            self.ser.baudate = baudrate
            self.ser.dtr=True
            self.ser.rts=True
            self.ser.open()

    # send a single string
    def send(self, string):
        msg = string.encode('ascii')
        totalsent = 0
        while totalsent < len(msg[totalsent:]) :
            sent = self.ser.write(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("serial connection broken")
            totalsent = totalsent + sent

    # receive at least one GridConnect frame and return as string.
    # Guarantee: If input is valid, there will be at least one ";" in the response.  
    # This makes it nicer to display the raw data.
    # Note that the response may end with a partial frame.
    def receive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.ser.read(size=1)  # can't wait for default newline
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
            if 0x3B in chunk : break
        return b''.join(chunks).decode("utf-8").replace("\n", "").replace("\r","")

