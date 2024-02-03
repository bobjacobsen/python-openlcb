'''
Simulated CanPhysicalLayer to record frames requested to be sent.
'''

from openlcb.canbus.canphysicallayer import CanPhysicalLayer


class CanPhysicalLayerSimulation(CanPhysicalLayer):

    def __init__(self):
        self.receivedFrames = []
        CanPhysicalLayer.__init__(self)

    def sendCanFrame(self, frame):
        self.receivedFrames.append(frame)
