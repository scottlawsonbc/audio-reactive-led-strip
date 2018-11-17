class Node(object):

    effect = None

    def __init__(self, effect):
        self.effect = effect

class Connection(object):
    fromNode = None
    toNode = None
    fromChannel = None
    toChannel = None

    def __init__(self, from_node, from_channel, to_node, to_channel):
        self.fromChannel = from_channel
        self.fromNode = from_node
        self.toChannel = to_channel
        self.toNode = to_node


class FilterGraph(object):

    _filterNodes = []
    _filterConnections = []

    def __init__(self):
        self._filterConnections = []
        self._filterNodes = []

    def update(self):
        None
    
    def process(self):
        None

    def addEffectNode(self, effect):
        """Adds a filter node to the graph

        Parameters
        ----------
        filterNode: node to add
        """
        self._filterNodes.append(Node(effect))

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
        

    def addConnection(self, fromEffect, fromEffectChannel, toEffect, toEffectChannel):
        """Adds a connection between two filters
        """
        # find fromNode
        fromNode = next(node for node in self._filterNodes if node.effect == fromEffect)
        # find toNode
        toNode = next(node for node in self._filterNodes if node.effect == toEffect)
        # construct connection
        self._filterConnections.append(Connection(fromNode, fromEffectChannel, toNode, toEffectChannel))
        
    
    def removeConnection(self, fromEffect, fromEffectChannel, toEffect, toEffectChannel):
        """Removes a connection between two filters
        """
        # find connection
        con = next(con for con in self._filterConnections if con.fromNode.effect == fromEffect and con.toNode.effect == toEffect and con.fromChannel == fromEffectChannel and con.toChannel == toEffectChannel)
        if con != None:
            self._filterConnections.remove(con)
        None