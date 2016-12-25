from __future__ import print_function
from __future__ import division
import time
import numpy as np
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg


class GUI:
    plot = []
    curve = []

    def __init__(self, width=800, height=450, title=''):
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title)
        self.win.resize(width, height)
        self.win.setWindowTitle(title)

    def add_plot(self, title):
        self.plot.append(self.win.addPlot(title=title))
        self.curve.append([])

    def add_curve(self, plot_index, pen=(255, 255, 255)):
        self.curve[plot_index].append(self.plot[plot_index].plot(pen=pen))


if __name__ == '__main__':
    N = 48
    gui = GUI(title='Test')
    # Sin plot
    gui.add_plot(title='Sin Plot')
    gui.add_curve(plot_index=0)
    gui.win.nextRow()
    # Cos plot
    gui.add_plot(title='Cos Plot')
    gui.add_curve(plot_index=1)

    while True:
        t = time.time()
        x = np.linspace(t, 2 * np.pi + t, N)
        gui.curve[0][0].setData(x=x, y=np.sin(x))
        gui.curve[1][0].setData(x=x, y=np.cos(x))
        gui.app.processEvents()
        time.sleep(1.0 / 30.0)
