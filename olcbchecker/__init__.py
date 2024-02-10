'''
Define common interface for compatibility checks.

This is a set of convenience methods wrapping
the setup and configure modules
'''

from queue import Empty

def trace() :
    return setup.configure.trace

def sendMessage(message) :
    if trace() >= 20 : print("SM: {}".format(message))
    setup.canLink.sendMessage(message)
    
def getMessage(timeout=0.8) :
    return setup.readQueue.get(True, timeout)

def purgeMessages(timeout=0.3):
    while True :
        try :
            received = getMessage(timeout) # timeout if no entries
        except Empty:
             break

def ownnodeid() :
    return setup.configure.ownnodeid

def targetnodeid() :
    return setup.configure.targetnodeid
    
def getTargetID(timeout=0.3) :
    '''
    If it hasn't already been specified, use a
    Verify Node cycle to get the NodeID of the DUT
    '''
    from openlcb.nodeid import NodeID
    from openlcb.message import Message
    from openlcb.mti import MTI

    from queue import Empty

    # Make sure we have a valid node ID for the device being checked (DBC).
    # This is somewhat redundant with what we're trying to check in some cases.
    if targetnodeid() is None:

        # send an VerifyNodes message to provoke response
        message = Message(MTI.Verify_NodeID_Number_Global, NodeID(ownnodeid()), None)
        sendMessage(message)

        # pull the received frames and get the source ID from first as remote NodeID
        destination = None
        while True :
            try :
                received = getMessage(timeout) # timeout if no entries
        
                if received.mti != MTI.Verified_NodeID and received.mti != MTI.Verified_NodeID_Simple :
                    continue # ignore other messages
                if destination is None : 
                    destination = received.source
            except Empty:
                break
        if trace() >= 20 : print ("DUT node ID: ", destination)
    else: # was provided in configure
        destination = NodeID(targetnodeid())
    purgeMessages()
    return destination

def isCheckPip() :
    '''
    Should this check against the PIP values?
    '''
    return setup.configure.checkpip
    
def gatherPIP(destination, timeout=0.3) :
    '''
    Get the PIP information from the DUT.
    If the result is None, the PIP values should not be checked.
    Otherwise, the result is a set of PIP enum values.
    '''    
    from openlcb.nodeid import NodeID
    from openlcb.message import Message
    from openlcb.mti import MTI
    from openlcb.pip import PIP

    from queue import Empty

    # Should we skip these checks?
    if not isCheckPip() : return None
    
    # Get the PIP information from the destination.
    # This is somewhat redundant with what we're trying to check in some cases.

    # Send a PIP Request 
    message = Message(MTI.Protocol_Support_Inquiry, NodeID(ownnodeid()), destination)
    sendMessage(message)

    # pull the received frames and get the PIP from the reply
    while True :
        try :
            received = getMessage(timeout) # timeout if no entries
            # is this a pip reply?
            if not received.mti == MTI.Protocol_Support_Reply : continue # wait for next
            # success!
            if trace() >= 30 :
                result = received.data[0] << 24 | \
                        received.data[1] << 16 | \
                        received.data[2] <<8|  \
                        received.data[3]
                print("PIP reports:")
                list = PIP.contentsNamesFromInt(result)
                for e in list :
                    print (" ",e)
            
            purgeMessages()
            return PIP.setContentsFromList(received.data)
        except Empty:
            print ("Failure - no reply to PIP request")
            return None

