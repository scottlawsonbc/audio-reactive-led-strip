from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from pyqtgraph.Qt import QtCore, QtGui, uic
import qdarkstyle
import pyqtgraph as pg

# Change the PyQtGraph defaults
pg.setConfigOption('foreground', '#eff0f1')
pg.setConfigOption('background', '#272822')


class MainWindow(QtGui.QMainWindow):
    settingsUpdated = QtCore.pyqtSignal(dict)
    """Emitted when user changes a GUI setting"""

    closing = QtCore.pyqtSignal()
    """Emitted when closeEvent is emitted"""

    isFullscreen = False


    def __init__(self, settings_dict=None):
        super(MainWindow, self).__init__()
        uic.loadUi('gui-with-plots.ui', self)
        self.setStyleSheet(qdarkstyle.load_stylesheet(pyside=False))
        # Apply initial settings
        if settings_dict is not None:
            self.applySettings(settings_dict)
        # No point having everything fail because we couldn't set an icon
        try:
            icon = QtGui.QIcon()
            icon.addFile('icons/48x48.png', QtCore.QSize(48, 48))
            self.setWindowIcon(icon)
        except IOError as e:
            print('Error setting application icon:', e)
        # Same hotkey that closes browser tabs
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)
        QtGui.QShortcut(QtGui.QKeySequence("Esc"), self, self.close)
        QtGui.QShortcut(QtGui.QKeySequence("F11"), self, self.fullscreenToggled)

    def closeEvent(self, event):
        self.closing.emit()
        event.accept()

    def applySettings(self, settings_dict):
        """Apply the dictionary values to the controls for user settings"""
        self.fps.setValue(settings_dict['fps'])
        self.pixels.setValue(settings_dict['pixels'])
        self.effect.setCurrentIndex(settings_dict['effect_index'])
        self.rise.setValue(settings_dict['rise'])
        self.fall.setValue(settings_dict['fall'])
        self.minFreq.setValue(settings_dict['min_freq'])
        self.maxFreq.setValue(settings_dict['max_freq'])
        self.fftBins.setValue(settings_dict['fft_bins'])

    def settingsChanged(self, val):
        """Slot called when a GUI setting has been changed"""
        settings = {
            'fps': self.fps.value(),
            'pixels': self.pixels.value(),
            'effect': str(self.effect.currentText()),
            'rise': self.rise.value(),
            'fall': self.fall.value(),
            'min_freq': self.minFreq.value(),
            'max_freq': self.maxFreq.value(),
            'fft_bins': self.fftBins.value()
        }
        self.settingsUpdated.emit(settings)

    def fullscreenToggled(self):
        """Toggles fullscreen mode on or off"""
        if self.isFullscreen:
            self.showFullScreen()
        else:
            self.showNormal()
        self.isFullscreen = not self.isFullscreen


if __name__ == '__main__':
    app = QtGui.QApplication([])
    win = MainWindow()
    win.show()
    while True:
        app.processEvents()
