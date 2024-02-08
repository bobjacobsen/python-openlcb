'''
Set up the Message level infrastructure, including 
an underlying CAN serial or TCP GridConnect layer

This runs when imported.
'''

from openlcb.canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from openlcb.canbus.canframe import CanFrame
from openlcb.canbus.canlink import CanLink
from openlcb.canbus.controlframe import ControlFrame

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP

from queue import Queue
from queue import Empty

# get and process options
import configure

# define common interface for message-level conformance checks

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

def receiveFrame(frame) : 
    if trace >= 30 : print("RL: "+str(frame) )
 
canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(receiveFrame)

def processMessage(msg):
    if trace >= 20 : print("RM: {} from {}".format(msg, msg.source))
    readQueue.put(msg)

canLink = CanLink(NodeID(configure.ownnodeid))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(processMessage)

readQueue = Queue()

# put the read on a separate thread
def receiveLoop() :
    # bring the CAN level up
    # print("      SL : link up")
    canPhysicalLayerGridConnect.physicalLayerUp()
    while True:
        input = s.receive()
        if trace >= 40 : print("   RR: "+input)
        # pass to link processor
        canPhysicalLayerGridConnect.receiveString(input)
import threading
thread = threading.Thread(daemon=True, target=receiveLoop)

# define a routine for checking tests
def result(arg1, arg2=None, arg3=None, result=True) :
    # returns True if OK, False if failed
    # If arg1 and arg2 provided
    #   compare those, and fail if not equal; arg3 is then message
    # If only arg1, report it and return result for fail value
    if arg2 is not None :
        if arg1 == arg2 :
            # OK
            print(arg1)
            return True
        else :
            print("{} does not equal {}, FAIL".format(arg1, arg2))
            return False
    else:
        print(arg1)
        return result

# start the process
thread.start()

