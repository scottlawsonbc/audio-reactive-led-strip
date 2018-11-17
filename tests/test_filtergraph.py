from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import unittest
import numpy as np
from audioled import filtergraph 

class MockEffect(object):
    def __init__(self):
        pass

class TestDSP(unittest.TestCase):

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

    def test_autoRemoveConnections(self):
        fg = filtergraph.FilterGraph()
        ef1 = MockEffect()
        ef2 = MockEffect()
        fg.addEffectNode(ef1)
        fg.addEffectNode(ef2)
        fg.addConnection(ef1,0,ef2,0)
        self.assertEqual(len(fg._filterConnections),1)
        fg.removeEffectNode(ef1)
        self.assertEqual(len(fg._filterConnections),0)