from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import unittest
import numpy as np
from audioled import dsp 


class TestDSP(unittest.TestCase):

    def test_fir_moving_average_1D(self):
        """Verify FIR filter output for 1D 3-point moving average"""
        taps = [1 / 3, 1 / 3, 1 / 3]
        data_in = np.arange(10)
        data_out = list(dsp.fir(taps, data_in))
        ismatch = np.isclose(data_out, np.arange(1, 9))
        self.assertTrue(ismatch.all())

    def test_fir_moving_average_2D(self):
        """Verify FIR filter output for 2D 3-point moving average"""
        taps = [1. / 3., 1. / 3., 1. / 3.]
        data_in = np.tile(np.arange(10), (3, 1)).T
        data_out = np.array(list(dsp.fir(taps, data_in)))
        ismatch = np.isclose(data_out, np.tile(np.arange(1, 9), (3, 1)).T)
        self.assertTrue(ismatch.all())


    # def test_warped_psd(self):
    #     import matplotlib.pyplot as plt
    #     plt.style.use('lawson')
    #     y = np.load('test-data/raw-audio-3.npy')[:256]
    #     y = np.random.normal(size=1024)
    #     energy = []
    #     bins = np.arange(1, 512, 1)
    #     for i in bins:
    #         mel = dsp.warped_psd(y, bins=i, fs=22050, frange=[0, 22050//2], scale='bark')
    #         energy.append(np.sum(mel))
    #         print(energy[-1])
    #     print(np.sum(y**2))
    #     plt.plot(bins, energy)
    #     plt.show()


    # def test_rollwin_output(self):
    #     """Verify correct rolling window output for rollwin generator"""
    #     # Verify output with an even window length
    #     data_in = [[0, 1, 2, 3], [4, 5, 6, 7]]
    #     validation = [2, 3, 4, 5, 6, 7]
    #     self.assertTrue((list(dsp.rollwin(data_in, 0.5)) == validation).all())
    #     # Verify output with an odd window length
    #     data_in = np.array([[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]])
    #     validation = np.array([[1, 2, 3], [3, 4, 5], [5, 6, 7], [7, 8, 9]])
    #     self.assertTrue((list(dsp.rollwin(data_in, 0.5)) == validation).all())

    def test_downsample(self):
        chunks = 3  # Number of chunks in signal
        samples = 5  # Number of samples per chunk
        N = chunks * samples
        signal = np.split(np.linspace(0, 1, N), chunks)
        signal = (chunk for chunk in signal)

        # Downsampling should not be possible when fs == 2 * fmax
        ds_signal, ds_fs = dsp.downsample(signal, fs=2, fmax=1)
        self.assertEqual(ds_fs, 2)

        # ValueError should be raised when fs < 2 * fmax
        self.assertRaises(ValueError, dsp.downsample, signal, 1, 1)

        # When fs == (4 * fmax) then we expect fs == (2 * ds_fs)
        ds_signal, ds_fs = dsp.downsample(signal, fs=4, fmax=1)
        self.assertEqual(ds_fs, 2)

        # Downsampling N values by 2x should return (N + (N % 2)) // 2 samples
        # Number of chunks in the signal should remain unchanged
        ds_signal, ds_fs = dsp.downsample(signal, fs=4, fmax=1)
        ds_signal = list(ds_signal)
        ds_samples = len(ds_signal[0])
        self.assertEqual(ds_samples, (samples + (samples % 2)) // 2)
        self.assertEqual(len(ds_signal), chunks)

    def test_pad_zeros(self):
        chunks = 7
        samples = 6
        signal = np.ones((chunks, samples))
        signal = (chunk for chunk in signal)
        padded = dsp.pad_zeros(signal)
        padded = np.array(list(padded))

        # Number of chunks should not be modified
        self.assertEqual(padded.shape[0], chunks)

        # Number of samples per chunk should be 8
        self.assertEqual(padded.shape[1], 8)

        # Last two elements should be 0
        self.assertTrue((padded[:, -2:] == 0).all())

        # First 8 elements should be 1
        self.assertTrue((padded[:, :-2] == 1).all())


    def test_normalize_scale(self):
        """Verifies that normalize_scale returns values in range 0 to 1"""
        signal = 2 * np.sin(np.linspace(0, 2 * np.pi, 128)) + 4
        signal = (frame for frame in signal)
        signal = dsp.normalize_scale(signal, past_n=10)
        signal = np.array(list(signal))
        self.assertTrue((signal <= 1.0).all())
        self.assertTrue((signal >= 0.0).all())
        self.assertTrue((signal == 0.0).any())
        self.assertTrue((signal == 1.0).any())

        # Verify that it doesn't fail when given constant values
        signal = (frame for frame in np.ones(8))
        signal = dsp.normalize_scale(signal, past_n=4)
        signal = np.array(list(signal))
        self.assertTrue((signal == 0).all())




if __name__ == '__main__':
    unittest.main()
