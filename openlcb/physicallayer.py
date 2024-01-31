'''
Generalize access to the physical layer;.

Parent of `CanPhysicalLayer`

'''


class PhysicalLayer:
    def physicalLayerUp(self):
        pass  # abstract method

    def physicalLayerRestart(self):
        pass  # abstract method

    def physicalLayerDown(self):
        pass  # abstract method
