'''
Set up the Frame level infrastructure, including 
an underlying CAN serial or TCP GridConnect layer

This runs when imported.
'''

from openlcb.canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from openlcb.canbus.canframe import CanFrame
from openlcb.canbus.canlink import CanLink
from openlcb.canbus.controlframe import ControlFrame

from openlcb.nodeid import NodeID

from queue import Queue
from queue import Empty

# get and process options
import configure

# define common interface for compatibility checks

trace = configure.trace # just to be shorter

# configure the physical link
if configure.hostname is not None : 
    from openlcb.canbus.tcpsocket import TcpSocket
    s = TcpSocket()
    s.connect(configure.hostname, configure.portnumber)
else :
    from openlcb.canbus.seriallink import SerialLink
    s = SerialLink()
    s.connect(configure.devicename)
    
if trace >= 20 :
    print("RR, SR are raw socket interface receive and send; RL, SL are link (frame) interface")

def sendToSocket(string) :
    if trace >= 40 : print("   SR: "+string)
    s.send(string)

def sendCanFrame(frame) :
    if trace >= 30 : print("SL: "+str(frame) )
    canPhysicalLayerGridConnect.sendCanFrame(frame)
    
def receiveFrame(frame) : 
    if trace >= 30 : print("RL: "+str(frame) )
    readQueue.put(frame)
 
canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(receiveFrame)

readQueue = Queue()

# put the read on a separate thread
def receiveLoop() :
    while True:
        input = s.receive()
        if trace >= 40 : print("   RR: "+input)
        # pass to link processor
        canPhysicalLayerGridConnect.receiveString(input)
import threading
thread = threading.Thread(daemon=True, target=receiveLoop)

# start the process
thread.start()

