from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from pyqtgraph.Qt import QtCore, QtGui, uic
import qdarkstyle
import pyqtgraph as pg
import config
# Change the PyQtGraph defaults
pg.setConfigOption('foreground', '#eff0f1')
pg.setConfigOption('background', '#272822')


class MainWindow(QtGui.QMainWindow):
    settingsUpdated = QtCore.pyqtSignal(dict)
    """Emitted when user changes a GUI setting"""

    closing = QtCore.pyqtSignal()
    """Emitted when closeEvent is emitted"""

    def __init__(self, settings_dict=None):
        super(MainWindow, self).__init__()
        uic.loadUi(config.GUI_UI_FILE_PATH, self)
        self.setStyleSheet(qdarkstyle.load_stylesheet(pyside=False))
        # Apply initial settings
        if settings_dict is not None:
            self.applySettings(settings_dict)
        # No point having everything fail because we couldn't set an icon
        try:
            icon = QtGui.QIcon()
            icon.addFile('icons/256x256.png', QtCore.QSize(256, 256))
            self.setWindowIcon(icon)
        except IOError as e:
            print('Error setting application icon:', e)
        # Add curves to plot
        self.initPlots()
        # Hotkeys for convenience
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)
        QtGui.QShortcut(QtGui.QKeySequence("Esc"), self, self.close)
        QtGui.QShortcut(QtGui.QKeySequence("h"), self, self.settingsToggled)

    def initPlots(self):
        self.plot1. setRange(yRange=[-0.1, 1.1])
        self.plot1.disableAutoRange(axis=pg.ViewBox.YAxis)
        r = pg.mkPen((255, 30, 30, 200), width=4)
        g = pg.mkPen((30, 255, 30, 200), width=4)
        b = pg.mkPen((30, 30, 255, 200), width=4)
        w = pg.mkPen((255, 255, 255, 200), width=1)
        colors = [r, g, b, w]
        curves = [pg.PlotCurveItem(pen=c) for c in colors]
        for curve in curves:
            self.plot1.addItem(curve)
        self.plot1.curves = curves

        self.img = pg.ImageItem()
        self.vb = self.plot2.addViewBox(row=1, col=1)
        self.vb.setContentsMargins(0, 0, 0, 0)
        self.vb.addItem(self.img)

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
        self.colormap.setCurrentIndex(settings_dict['cmap_index'])

    def settingsChanged(self, val=None):
        """Slot called when a GUI setting has been changed"""
        settings = {
            'fps': self.fps.value(),
            'pixels': self.pixels.value(),
            'effect': str(self.effect.currentText()),
            'rise': self.rise.value(),
            'fall': self.fall.value(),
            'min_freq': self.minFreq.value(),
            'max_freq': self.maxFreq.value(),
            'fft_bins': self.fftBins.value(),
            'show_plot': self.showPlot.isChecked(),
            'cmap': str(self.colormap.currentText())
        }
        self.settingsUpdated.emit(settings)

    def showPlotToggled(self, show_plot):
        # self.plot1.show() if show_plot else self.plot1.hide()
        self.plotSplitter.show() if show_plot else self.plotSplitter.hide()
        self.resize(self.sizeHint())

    def settingsToggled(self):
        if self.settingsFrame.isVisible():
            self.settingsFrame.hide()
        else:
            self.settingsFrame.show()

    def fullscreenToggled(self, isFullscreen):
        """Toggles fullscreen mode on or off"""
        self.showFullScreen() if isFullscreen else self.showNormal()


if __name__ == '__main__':
    app = QtGui.QApplication([])
    win = MainWindow()
    win.show()
    app.exec_()
