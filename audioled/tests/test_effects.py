from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
import time
import unittest
import numpy as np
import audioled.effects as effects



    def _spectrum_output(self, N=60, fs=44100, chunk_rate=60, duration=1):
        chunks = chunk_rate * duration
        audio = (np.random.random(fs // chunk_rate) for _ in range(chunks))
        effect = effects.spectrum(pixels=N, fs=fs, chunk_rate=chunk_rate)
        return [pixels for pixels in effect(audio)]

    def test_spectrum_return_shape(self):
        """Verify output has 3 rows and N columns, N = number of pixels"""
        N = 60
        [self.assertEqual(x.shape, (3, N)) for x in self._spectrum_output(N)]

    def test_spectrum_return_dtype(self):
        """Verify output has integer dtype"""
        [self.assertEqual(x.dtype, int) for x in self._spectrum_output()]

    def test_spectrum_pixel_brightness(self):
        """Verify that there is actual output and not just zeros"""
        N = 60
        min_avg_brightness = 50
        max_avg_brightness = 225
        brightness = [np.mean(x) for x in self._spectrum_output(N)]
        brightness = sum(brightness) / len(brightness)
        self.assertGreaterEqual(brightness, min_avg_brightness)
        self.assertLessEqual(brightness, max_avg_brightness)

    def test_spectrum_real_time_factor(self):
        """Verify that spectrum effect satisfies the real-time constraint"""
        # Real-time factor is the ratio (actual time) / (execution time)
        # Real-time factor >> 1 is ideal and 1 is the absolute minimum
        audio_duration = 10
        t0 = time.clock()
        self._spectrum_output(N=300, fs=44100, chunk_rate=90,
                              duration=audio_duration)
        execution_time = time.clock() - t0
        min_factor = 5
        real_time_factor = audio_duration / execution_time
        print('Real-time factor:', round(real_time_factor, 2))
        self.assertGreater(real_time_factor, min_factor)


if __name__ == '__main__':
    unittest.main()
