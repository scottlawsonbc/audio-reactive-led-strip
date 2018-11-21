class Effect(object):
    def __init__(self):
        self.t = 0.0
        self._inputBuffer = None
        self._outputBuffer = None

    def numOutputChannels(self):
        raise NotImplementedError('update() was not implemented')

    def numInputChannels(self):
        raise NotImplementedError('update() was not implemented')

    def setOutputBuffer(self,buffer):
        self._outputBuffer = buffer

    def setInputBuffer(self, buffer):
        self._inputBuffer = buffer

    def process(self):
        raise NotImplementedError('update() was not implemented')
    
    def update(self, dt):
        self.t += dt

class Node(object):

    def __init__(self, effect):
        self.effect = effect
        self.outputBuffer = [None for i in range(0, effect.numOutputChannels())]
        self.inputBuffer = [None for i in range(0, effect.numInputChannels())]
        self.incomingConnections = []

        effect.setOutputBuffer(self.outputBuffer)
        effect.setInputBuffer(self.inputBuffer)

    def process(self):
        # propagate values
        for con in self.incomingConnections:
            self.inputBuffer[con.toChannel] = con.fromNode.outputBuffer[con.fromChannel]
        # process
        self.effect.process()
    
    def update(self, dt):
        self.effect.update(dt)

class Connection(object):

    def __init__(self, from_node, from_channel, to_node, to_channel):
        self.fromChannel = from_channel
        self.fromNode = from_node
        self.toChannel = to_channel
        self.toNode = to_node


class FilterGraph(object):

    def __init__(self):
        self._filterConnections = []
        self._filterNodes = []
        self._processOrder = []

    def update(self, dt):
        for node in self._processOrder:
            node.update(dt)
    
    def process(self):
        for node in self._processOrder:
            node.process()

    def addEffectNode(self, effect):
        """Adds a filter node to the graph

        Parameters
        ----------
        filterNode: node to add
        """
        node = Node(effect)
        self._filterNodes.append(node)
        self._updateProcessOrder()
        return node

    def removeEffectNode(self, effect):
        """Removes a filter node from the graph

        Parameters
        ----------
        filterNode: node to remove
        """
        # Remove connections
        connections = [con for con in self._filterConnections if con.fromNode.effect == effect or con.toNode.effect == effect]
        for con in connections:
            self._filterConnections.remove(con)
        # Remove Node
        node = next(node for node in self._filterNodes if node.effect == effect)
        if node != None:
            self._filterNodes.remove(node)
            self._processOrder.remove(node)
        

    def addConnection(self, fromEffect, fromEffectChannel, toEffect, toEffectChannel):
        """Adds a connection between two filters
        """
        # find fromNode
        fromNode = next(node for node in self._filterNodes if node.effect == fromEffect)
        # find toNode
        toNode = next(node for node in self._filterNodes if node.effect == toEffect)
        # construct connection
        newConnection = Connection(fromNode, fromEffectChannel, toNode, toEffectChannel)
        self._filterConnections.append(newConnection)
        toNode.incomingConnections.append(newConnection)
        self._updateProcessOrder()
        
    
    def removeConnection(self, fromEffect, fromEffectChannel, toEffect, toEffectChannel):
        """Removes a connection between two filters
        """
        # find connection
        con = next(con for con in self._filterConnections if con.fromNode.effect == fromEffect and con.toNode.effect == toEffect and con.fromChannel == fromEffectChannel and con.toChannel == toEffectChannel)
        if con != None:
            self._filterConnections.remove(con)
            con.toNode.incomingConnections.remove(con)
        None
    
    def _updateProcessOrder(self):
        # reset
        self._processOrder = []
        # find nodes without inputs
        allNodes = self._filterNodes.copy()
        for con in self._filterConnections:
            if allNodes.count(con.toNode) > 0:
                allNodes.remove(con.toNode)
        
        # Add those nodes first
        for node in allNodes:
            self._processOrder.append(node)
        
        #print("{} of {} nodes without inputs processed".format(len(self._processOrder), len(self._filterNodes)))

        # Process others
        connectionsToProcess = self._filterConnections.copy()
        while len(connectionsToProcess) > 0:
            nodesBefore = len(self._processOrder)
            # find nodes with connections only relying on nodes already in chain
            candidates = self._filterNodes.copy()
            for node in self._processOrder:
                candidates.remove(node)
            
            # if we find a connection with anything other than input nodes already processed, those are not candidates

            for con in connectionsToProcess:
                if self._processOrder.count(con.fromNode) <= 0 and candidates.count(con.toNode) > 0:
                    candidates.remove(con.toNode)
            
            # append all candidates
            for node in candidates:
                self._processOrder.append(node)
            
            # update connections to process
            for con in connectionsToProcess.copy():
                if self._processOrder.count(con.fromNode) > 0 and self._processOrder.count(con.toNode) > 0:
                    connectionsToProcess.remove(con)

            #print("{} of {} nodes processed".format(len(self._processOrder), len(self._filterNodes)))

            if len(self._processOrder) == nodesBefore:
                print("circular graph detected")
                raise RuntimeError("circular graph detected")

        if len(self._processOrder) != len(self._filterNodes):
            raise RuntimeError("not all nodes processed")


