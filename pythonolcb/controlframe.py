# an Enum representing the various kinds of CAN control frames.

from enum import Enum

# these are link-layer concepts, so below here instead of CanFrame
class ControlFrame(Enum) : 
    RID = 0x0700
    AMD = 0x0701
    AME = 0x0702
    AMR = 0x0703
    EIR0 = 0x00710
    EIR1 = 0x00711
    EIR2 = 0x00712
    EIR3 = 0x00713
    
    # note these two don't code the entire control field value (i.e. there are arguments in the lower bits)
    CID  =  0x4000
    Data = 0x18000

    # these are non-OLCB values used for internal signaling
    # their values have a bit set above what can come from a CAN Frame
    LinkUp         = 0x20000
    LinkRestarted  = 0x20001
    LinkCollision  = 0x20002
    LinkError      = 0x20003
    LinkDown       = 0x20004
    UnknownFormat  = 0x21000

