from __future__ import print_function
from __future__ import division
import time
import numpy as np
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
from pyqtgraph.dockarea import *


class GUI:
    plot = []
    curve = []

    def __init__(self, width=800, height=450, title=''):
        # Create GUI window
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title)
        self.win.resize(width, height)
        self.win.setWindowTitle(title)
        # Create GUI layout
        self.layout = QtGui.QVBoxLayout()
        self.win.setLayout(self.layout)

    def add_plot(self, title):
        new_plot = pg.PlotWidget()
        self.layout.addWidget(new_plot)
        self.plot.append(new_plot)
        self.curve.append([])

    def add_curve(self, plot_index, pen=(255, 255, 255)):
        self.curve[plot_index].append(self.plot[plot_index].plot(pen=pen))


if __name__ == '__main__':
    # Example test gui
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
