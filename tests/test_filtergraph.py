from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import unittest
import numpy as np
from audioled import filtergraph 



class Test_FilterGraph(unittest.TestCase):

    def test_canAddAndRemoveNodes(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        ef2 = MockEffect()

        fg.addEffectNode(ef1)
        self.assertEqual(len(fg._filterNodes),1)
        fg.addEffectNode(ef2)
        self.assertEqual(len(fg._filterNodes),2)
        fg.removeEffectNode(ef1)
        self.assertEqual(len(fg._filterNodes),1)
        fg.removeEffectNode(ef2)
        self.assertEqual(len(fg._filterNodes),0)
    
    def test_canAddRemoveNodeConnections(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        ef2 = MockEffect()

        fg.addEffectNode(ef1)
        fg.addEffectNode(ef2)
        fg.addConnection(ef1,0,ef2,0)
        self.assertEqual(len(fg._filterConnections),1)
        fg.removeConnection(ef1,0,ef2,0)
        self.assertEqual(len(fg._filterConnections),0)

    def test_connectionOrder_ok(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        ef2 = MockEffect()
        ef3 = MockEffect()
        
        n1 = fg.addEffectNode(ef1)
        
        n2 = fg.addEffectNode(ef2)
        
        n3 = fg.addEffectNode(ef3)
        
        fg.addConnection(ef1,0,ef2,0)
        fg.addConnection(ef2,0,ef3,0)

        self.assertTrue(fg._processOrder.index(n1) < fg._processOrder.index(n2))
        self.assertTrue(fg._processOrder.index(n1) < fg._processOrder.index(n3))
        self.assertTrue(fg._processOrder.index(n2) < fg._processOrder.index(n3))

    def test_removeNodes_connectionsAreRemove(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        ef2 = MockEffect()
        fg.addEffectNode(ef1)
        fg.addEffectNode(ef2)
        fg.addConnection(ef1,0,ef2,0)
        self.assertEqual(len(fg._filterConnections),1)
        fg.removeEffectNode(ef1)
        self.assertEqual(len(fg._filterConnections),0)

    def test_circularConnections_raisesError(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        ef2 = MockEffect()
        ef3 = MockEffect()
        fg.addEffectNode(ef1)
        fg.addEffectNode(ef2)
        fg.addEffectNode(ef3)
        fg.addConnection(ef1,0,ef2,0)
        fg.addConnection(ef2,0,ef3,0)
        self.assertRaises(RuntimeError, fg.addConnection, ef3,0,ef1,0)

    def test_outputBuffer_works(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        fg.addEffectNode(ef1)
        fg.process()
        self.assertEqual(len(fg._filterNodes[0].outputBuffer), 5)
        self.assertEqual(fg._filterNodes[0].outputBuffer[0], 0)
    
    def test_mockEffect_works(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        n1 = fg.addEffectNode(ef1)
        ef1._inputBuffer[0] = 'test'
        ef1.process()
        self.assertEqual(ef1._outputBuffer[0], 'test')

        n1.inputBuffer[0] = 'test2'
        fg.process()
        self.assertEqual(ef1._outputBuffer[0], 'test2')
        self.assertEqual(n1.outputBuffer[0], 'test2')


    def test_valuePropagation_works(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        ef2 = MockEffect()

        n1 = fg.addEffectNode(ef1)
        n2 = fg.addEffectNode(ef2)
        fg.addConnection(ef1,0,ef2,1)

        n1.inputBuffer[0] = 'test'
        fg.process()

        self.assertEqual(n1.outputBuffer[0], 'test')
        self.assertEqual(n2.outputBuffer[1], 'test')


class MockEffect(object):

    def __init__(self):
        self._outputBuffer = None
        self._inputBuffer = None

    def numOutputChannels(self):
        return 5

    def numInputChannels(self):
        return 5
    
    def setOutputBuffer(self,buffer):
        self._outputBuffer = buffer
    def setInputBuffer(self, buffer):
        self._inputBuffer = buffer

    def process(self):
        self._outputBuffer[0] = 0
        self._outputBuffer[1] = 1
        self._outputBuffer[2] = 2
        self._outputBuffer[3] = 3
        self._outputBuffer[4] = 4

        for i in range(0,5):
            if self._inputBuffer[i] != None:
                self._outputBuffer[i] = self._inputBuffer[i]