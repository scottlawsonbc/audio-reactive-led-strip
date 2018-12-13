from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import unittest
import numpy as np
from audioled import effects

class Test_Effects(unittest.TestCase):
    def test_effectDoesntProcessNullBuffers(self):
        effect = effects.Mirror()
        effect.process()
        self.assertIsNone(effect._inputBuffer)
    # Disabled because implementation has changed and test is out of scope for now 
    #
    # def test_mirrorEffect(self):
    #     n=3
    #     rgb = np.linspace(0,n,n) * np.array([[1.0],[2.0],[3.0]])
    #     print(rgb)
    #     mapMask = np.array([[[0,i] for i in range(0,n)],
    #                         [[1,i] for i in range(0,n)],
    #                         [[2,i] for i in range(0,n)]],dtype=np.int64)
    #     print(mapMask)
    #     # revert
    #     mapMask = mapMask[:,::-1,:]
    #     # revert again
    #     mapMask = mapMask[:,::-1,:]
    #     print(mapMask)
    #     mapped = rgb[mapMask[:,:,0], mapMask[:,:,1]]
    #     print(mapped)
    #     np.testing.assert_array_equal(mapped, rgb)
        
    #     mirror = effects.Mirror(mirror_lower = True, recursion = 0)
    #     mirror._inputBuffer = []
    #     mirror._outputBuffer = []
    #     mirror._inputBuffer.append((np.ones(4) * np.array([[0],[0],[0]])))
    #     mirror.update(0)
    #     mirror._outputBuffer.append((np.ones(4) * np.array([[0],[0],[0]])))
    #     mirror.process()
    #     print(mirror._mirrorLower)
    #     np.testing.assert_array_equal(mirror._mirrorLower[0,:,1],np.array([0,1,1,0]))
        
    #     mirror = effects.Mirror(mirror_lower = True,recursion = 1)
    #     np.testing.assert_array_equal(mirror._mirrorLower[0,:,1],np.array([0,1,1,0,0,1,1,0]))



    #     mirror = effects.Mirror(mirror_lower = True,recursion = 2)
    #     np.testing.assert_array_equal(mirror._mirrorLower[0,:,1],np.array([0,1,1,0,0,1,1,0,3, 2, 2, 3, 3, 2, 2, 3]))


