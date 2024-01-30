'''
Generalize a CAN physical layer, real or simulated.

This is a class because it represents a single physical connection to a layout
and is subclassed.
'''
from canbus.canframe import CanFrame
from openlcb.controlframe import ControlFrame
from openlcb.physicallayer import PhysicalLayer


class CanPhysicalLayer(PhysicalLayer):

    def __init__(self):
        self.listeners = []

    def sendCanFrame(self, frame):
        '''basic abstract interface'''
        pass

    def registerFrameReceivedListener(self, listener):
        self.listeners.append(listener)

    def fireListeners(self, frame):
        for listener in self.listeners:
            listener(frame)

    def physicalLayerUp(self):
        '''Invoked when the physical link implementation has initially come up
        '''
        # notify link layer
        cf = CanFrame(ControlFrame.LinkUp.value, 0)
        self.fireListeners(cf)

    def physicalLayerRestart(self):
        '''Invoked from OpenlcbNetwork when the physical link implementation
        has come up 2nd or later times
        '''
        # notify link layer
        cf = CanFrame(ControlFrame.LinkRestarted.value, 0)
        self.fireListeners(cf)

    def physicalLayerDown(self):
        '''Invoked from OpenlcbNetwork when the physical link implementation
        has gone down
        '''
        # notify link layer
        cf = CanFrame(ControlFrame.LinkDown.value, 0)
        self.fireListeners(cf)
