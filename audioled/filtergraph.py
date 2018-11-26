import asyncio
from timeit import default_timer as timer
import numpy as np

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
    
    async def update(self, dt):
        await self.effect.update(dt)

class Connection(object):

    def __init__(self, from_node, from_channel, to_node, to_channel):
        self.fromChannel = from_channel
        self.fromNode = from_node
        self.toChannel = to_channel
        self.toNode = to_node

class Timing(object):
    def __init__(self):
        self._max = None
        self._min = None
        self._avg = None
        self._count = 0
    
    def update(self, timing):
        if self._count == 0:
            self._max = timing
            self._min = timing
            self._avg = timing
        else:
            self._max = max(self._max, timing)
            self._min = min(self._min, timing)
            self._avg = (self._avg * self._count + timing) / (self._count + 1)
        self._count = self._count + 1
        self._count = max(100, self._count)


class FilterGraph(object):

    def __init__(self, recordTimings=False):
        self.recordTimings=recordTimings
        self._filterConnections = []
        self._filterNodes = []
        self._processOrder = []
        self._updateTimings = {}
        self._processTimings = {}

    def update(self, dt):
        time = timer()
        loop = asyncio.get_event_loop()



        #loop.run_until_complete(asyncio.wait(tasks))  
        #loop.
        # close()
        all_tasks = asyncio.gather(*[asyncio.ensure_future(node.update(dt)) for node in self._processOrder])
        results = loop.run_until_complete(all_tasks)

        print("Update time: {}".format(timer() - time))

        #loop.close()

        # for node in self._processOrder:
        #     if self.recordTimings:
        #         time = timer()
        #     node.update(dt)
        #     if self.recordTimings:
        #         self.updateUpdateTiming(node, timer() - time)
    
    def process(self):
        time = None

        for node in self._processOrder:
            if self.recordTimings:
                time = timer()
            node.process()
            if self.recordTimings:
                self.updateProcessTiming(node, timer() - time)

    def updateProcessTiming(self,node,timing):
        if not node in self._processTimings:
            self._processTimings[node] = Timing()
        
        self._processTimings[node].update(timing)

    def updateUpdateTiming(self,node,timing):
        if not node in self._updateTimings:
            self._updateTimings[node] = Timing()
        
        self._updateTimings[node].update(timing)

    def printUpdateTimings(self):
        if self._updateTimings is None:
            print("No metrics collected")
            return
        print("Update timings:")
        for key, val in self._updateTimings.items():
            print("{0}: min {1:1.8f}, max {2:1.8f}, avg {3:1.8f}".format(key.effect, val._min, val._max, val._avg))
    
    def printProcessTimings(self):
        if self._processTimings is None:
            print("No metrics collected")
            return
        print("Process timings:")
        for key, val in self._processTimings.items():
            print("{0:30s}: min {1:1.8f}, max {2:1.8f}, avg {3:1.8f}".format(str(key.effect)[0:30], val._min, val._max, val._avg))


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

    def __getstate__(self):
        state = {}
        effects = [node.effect for node in self._filterNodes]
        state['effects'] = effects
        connections = []
        for con in self._filterConnections:
            conDict = {}
            # find index of effect of fromNode in effects
            conDict['from_effect_idx'] = effects.index(con.fromNode.effect)
            conDict['from_channel'] = con.fromChannel
            conDict['to_effect_idx'] = effects.index(con.toNode.effect)
            conDict['to_channel'] = con.toChannel
            connections.append(conDict)
        state['connections'] = connections
        return state

    def __setstate__(self, state):
        self.__init__()
        effects = state['effects']
        for effect in effects:
            self.addEffectNode(effect)
        connections = state['connections']
        for con in connections:
            fromEffect = self._filterNodes[con['from_effect_idx']].effect
            fromChannel = con['from_channel']
            toEffect = self._filterNodes[con['to_effect_idx']].effect
            toChannel = con['to_channel']
            self.addConnection(fromEffect, fromChannel, toEffect, toChannel)
        
        
