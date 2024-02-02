
class LocalEventStore :
    '''
    Store node-specific Event information
    '''

    def __init__(self) :
        self.eventsConsumed=set(())
        self.eventsProduced=set(())
        
    def consumes(self, id) :
        self.eventsConsumed.add(id)
    
    def isConsumed(self, id) :
        return id in self.eventsConsumed
    
    def produces(self, id) :
        self.eventsProduced.add(id)
    
    def isProduced(self, id) :
        return id in self.eventsProduced

