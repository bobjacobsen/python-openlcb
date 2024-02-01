import unittest

from tcplink.tcplink import TcpLink

from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.nodeid import NodeID


class TcpMockLayer():
    def __init__(self):
        self.receivedText = []

    def send(self, text):
        self.receivedText.append(text)


class MessageMockLayer:
    '''Mock Message to record messages requested to be sent'''
    def __init__(self):
        self.receivedMessages = []

    def receiveMessage(self, msg):
        self.receivedMessages.append(msg)


class TestCanLinkClass(unittest.TestCase):

    def testLinkUpSequence(self):
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
        
        linkLayer.linkUp()

        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)

    def testLinkRestartSequence(self):
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
        
        linkLayer.linkRestarted()

        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)

    def testLinkDownSequence(self):
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
        
        linkLayer.linkDown()

        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        
    def testOneMessageOnePartOneClump(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
    
        messageText =  [0x80, 0x00,                      # full message
                        0x00, 0x00, 20,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00, 0x00,                      # MTI: VerifyNode
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21  # source NodeID
                        ]
        linkLayer.receiveListener(messageText)                
        
        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        print(messageLayer.receivedMessages[0].source)
        self.assertEqual(messageLayer.receivedMessages[0].source, NodeID(0x321))
        
    def testOneMessageOnePartTwoClumps(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
    
        messageText =  [0x80, 0x00,                      # full message
                        0x00, 0x00, 20,
                       ]
        linkLayer.receiveListener(messageText)                

        messageText =  [0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00, 0x00,                      # MTI: VerifyNode
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21  # source NodeID
                        ]
        linkLayer.receiveListener(messageText)                
        
        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        self.assertEqual(messageLayer.receivedMessages[0].source, NodeID(0x321))
        
    def testOneMessageOnePartThreeClumps(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
    
        messageText =  [0x80, 0x00,                      # full message
                        0x00, 0x00, 20,
                       ]
        linkLayer.receiveListener(messageText)                

        messageText =  [0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                       ]
                       
        linkLayer.receiveListener(messageText)                
        messageText =  [0x00, 0x00,                      # MTI: VerifyNode
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21  # source NodeID
                        ]
        linkLayer.receiveListener(messageText)                
        
        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        self.assertEqual(messageLayer.receivedMessages[0].source, NodeID(0x321))

    def testTwoMessageOnePartTwoClumps(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
    
        messageText =  [0x80, 0x00,                      # full message
                        0x00, 0x00, 20,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00, 0x00,                      # MTI: VerifyNode
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21  # source NodeID
                        ]
        linkLayer.receiveListener(messageText)                

        messageText =  [0x80, 0x00,                      # full message
                        0x00, 0x00, 20,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00, 0x00,                      # MTI: VerifyNode
                        0x00, 0x00, 0x00, 0x00, 0x04, 0x56  # source NodeID
                        ]
        linkLayer.receiveListener(messageText)                
        
        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 2)
        self.assertEqual(messageLayer.receivedMessages[0].source, NodeID(0x321))
        self.assertEqual(messageLayer.receivedMessages[1].source, NodeID(0x456))
        
    def testOneMessageTwoPartsOneClump(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
    
        messageText =  [0x80, 0x40,                      # part 1
                        0x00, 0x00, 13,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00,                      # first half MTI
                        
                        0x80, 0x80,                      # part 2
                        0x00, 0x00, 19,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00,                      # second half MTI
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21  # source NodeID
                        ]
        linkLayer.receiveListener(messageText)                
        
        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        self.assertEqual(messageLayer.receivedMessages[0].source, NodeID(0x321))
        
    def testOneMessageThreePartsOneClump(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
        linkLayer.linkPhysicalLayer(tcpLayer)
    
        messageText =  [0x80, 0x40,                      # part 1
                        0x00, 0x00, 13,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00,                      # first half MTI
                        
                        0x80, 0xC0,                      # part 2
                        0x00, 0x00, 13,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00,                      # second half MTI
                                                        # no data

                        0x80, 0x80,                      # part 3
                        0x00, 0x00, 18,
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,  # source node ID
                        0x00, 0x00, 0x11, 0x00, 0x00, 0x00,  # time
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21  # source NodeID
                        ]
        linkLayer.receiveListener(messageText)                
        
        self.assertEqual(len(tcpLayer.receivedText), 0)
        self.assertEqual(len(messageLayer.receivedMessages), 1)
        self.assertEqual(messageLayer.receivedMessages[0].source, NodeID(0x321))
        
    def testSendGlobalMessage(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
        linkLayer.linkPhysicalLayer(tcpLayer)
  
        message = Message(MTI.Verify_NodeID_Number_Global, NodeID(0x123), None, NodeID(0x321).toArray())
        linkLayer.sendMessage(message)
        
        self.assertEqual(len(tcpLayer.receivedText), 1)
        self.assertEqual(tcpLayer.receivedText[0][0:11],[ # can't check time
                        0x80, 0x00, 
                        0x00, 0x00, 26,
                        0x00, 0x00, 0x00, 0x00, 0x00, 100,
                        ])
        self.assertEqual(tcpLayer.receivedText[0][17:],[ # can't check time
                        0x04, 0x90,     # MTI
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21,
                        ])
        self.assertEqual(len(messageLayer.receivedMessages), 0)
    
    def testSendAddressedMessage(self) :
        messageLayer = MessageMockLayer()
        tcpLayer = TcpMockLayer()

        linkLayer = TcpLink(NodeID(100))
        linkLayer.registerMessageReceivedListener(messageLayer.receiveMessage)
        linkLayer.linkPhysicalLayer(tcpLayer)
  
        message = Message(MTI.Verify_NodeID_Number_Addressed, NodeID(0x123), NodeID(0x321), NodeID(0x321).toArray())
        linkLayer.sendMessage(message)
        
        self.assertEqual(len(tcpLayer.receivedText), 1)
        self.assertEqual(tcpLayer.receivedText[0][0:11],[ # can't check time
                        0x80, 0x00, 
                        0x00, 0x00, 32,
                        0x00, 0x00, 0x00, 0x00, 0x00, 100,
                        ])
        self.assertEqual(tcpLayer.receivedText[0][17:],[ # can't check time
                        0x04, 0x88,     # MTI
                        0x00, 0x00, 0x00, 0x00, 0x01, 0x23,
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21,
                        0x00, 0x00, 0x00, 0x00, 0x03, 0x21,
                        ])
        self.assertEqual(len(messageLayer.receivedMessages), 0)
    

if __name__ == '__main__':
    unittest.main()
