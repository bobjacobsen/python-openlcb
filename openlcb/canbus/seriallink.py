'''
simple serial input for string send and receive
expects prior setting of device name
'''
import serial

MSGLEN = 35


class SerialLink:
    """simple serial input for string send and receive"""
    def __init__(self):
        pass

    def connect(self, device, baudrate=230400):
        """Connect to a serial port.

        Args:
            device (str): A string that identifies a serial port for the
                serial.Serial constructor.
            baudrate (int, optional): Desired serial speed. Defaults to
                230400 bits per second.
        """
        self.port = serial.Serial(device, baudrate)
        self.port.reset_input_buffer()  # drop anything that's just sitting there already  # noqa: E501

    def send(self, string):
        """send a single string

        Args:
            string (str): Any string.

        Raises:
            RuntimeError: If the string couldn't be written to the port.
        """
        msg = string.encode('ascii')
        totalsent = 0
        while totalsent < len(msg[totalsent:]):
            sent = self.port.write(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        '''Receive at least one GridConnect frame and return as string.

        - Guarantee: If input is valid, there will be at least one ";"
          in the response.

        - This makes it nicer to display the raw data.

        - Note that the response may end with a partial frame.

        Returns:
            str: A GridConnect frame as a string.
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
        return (b''.join(chunks)).decode("utf-8")
