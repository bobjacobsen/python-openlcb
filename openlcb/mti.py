from enum import Enum


class MTI(Enum):

    Initialization_Complete            = 0x0100
    Initialization_Complete_Simple     = 0x0101
    Verify_NodeID_Number_Addressed     = 0x0488
    Verify_NodeID_Number_Global        = 0x0490
    Verified_NodeID                    = 0x0170
    Verified_NodeID_Simple             = 0x0171
    Optional_Interaction_Rejected      = 0x0068
    Terminate_Due_To_Error             = 0x00A8

    Protocol_Support_Inquiry           = 0x0828
    Protocol_Support_Reply             = 0x0668

    Identify_Consumer                  = 0x08F4
    Consumer_Range_Identified          = 0x04A4
    Consumer_Identified_Unknown        = 0x04C7
    Consumer_Identified_Active         = 0x04C4
    Consumer_Identified_Inactive       = 0x04C5
    Identify_Producer                  = 0x0914
    Producer_Range_Identified          = 0x0524
    Producer_Identified_Unknown        = 0x0547
    Producer_Identified_Active         = 0x0544
    Producer_Identified_Inactive       = 0x0545
    Identify_Events_Addressed          = 0x0968
    Identify_Events_Global             = 0x0970
    Learn_Event                        = 0x0594
    Producer_Consumer_Event_Report     = 0x05b4

    Simple_Node_Ident_Info_Request     = 0x0DE8
    Simple_Node_Ident_Info_Reply       = 0x0A08

    Remote_Button_Request              = 0x0948
    Remote_Button_Reply                = 0x0549

    Traction_Control_Command           = 0x05EB
    Traction_Control_Reply             = 0x01E9

    Datagram                           = 0x1C48
    Datagram_Received_OK               = 0x0A28
    Datagram_Rejected                  = 0x0A48

    Unknown                            = 0x0008   # make this addressed so that it;s individually processed

    # These are used for internal signalling and are not present in the MTI
    # specification.
    Link_Layer_Up                      = 0x2000   # entered Permitted state; needs to be marked global
    Link_Layer_Quiesce                 = 0x2010   # Link needs to be drained, will come back with Link_Layer_Restarted next
    Link_Layer_Restarted               = 0x2020   # link cycled without change of node state; needs to be marked global
    Link_Layer_Down                    = 0x2030   # entered Inhibited state; needs to be marked global

    New_Node_Seen                      = 0x2048   # alias resolution found new node; marked addressed (0x8 bit)

    def priority(self): return (self.value & 0x0C00) >> 10

    def addressPresent(self): return (self.value & 0x0008) != 0

    def eventIDPresent(self): return (self.value & 0x0004) != 0

    def simpleProtocol(self): return (self.value & 0x0010) != 0

    def isGlobal(self): return (self.value & 0x0008) == 0
