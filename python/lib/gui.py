#from __future__ import print_function
#from __future__ import division
#from scipy.ndimage.filters import gaussian_filter1d
#from collections import deque
#import time
#import sys
import numpy as np
import lib.config as config
#import microphone
#import dsp
#import led
#import random

from lib.qrangeslider import QRangeSlider
from lib.qfloatslider import QFloatSlider
import pyqtgraph as pg
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
       
class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('settings.ini', QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)    # File only, no fallback to registry or or.
        self.initUI()

    def hideGraphs(self):
        print("Blah")

    def hideOpts(self):
        print("Bleh")

    def config.settings["configuration"]["configDialogue"](self):
        self.d = QDialog(None, Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        b1 = QPushButton("ok",self.d)
        b1.move(50,50)
        self.d.setWindowTitle("Dialog")
        self.d.setWindowModality(Qt.ApplicationModal)
        self.d.show()
        
    def initUI(self):
        # ==================================== Set up window and wrapping layout
        self.setWindowTitle("Visualization")
        wrapper = QVBoxLayout()

        # ======================================================= Set up toolbar
        #toolbar_hideGraphs.setShortcut('Ctrl+H')
        toolbar_hideGraphs = QAction('GUI Properties', self)
        toolbar_hideGraphs.triggered.connect(self.config.settings["configuration"]["configDialogue"])
        toolbar_hideOpts = QAction('Hide Opts', self)
        toolbar_hideOpts.triggered.connect(self.hideOpts)
        
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(toolbar_hideGraphs)
        self.toolbar.addAction(toolbar_hideOpts)

        # ========================================== Set up FPS and error labels
        labels_layout = QHBoxLayout()
        self.label_error = QLabel("")
        self.label_fps = QLabel("")
        self.label_latency = QLabel("")
        self.label_fps.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label_latency.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        labels_layout.addWidget(self.label_error)
        labels_layout.addStretch()
        labels_layout.addWidget(self.label_latency)
        labels_layout.addWidget(self.label_fps)
        
        # ================================================== Set up graph layout
        graph_view = pg.GraphicsView()
        graph_layout = pg.GraphicsLayout(border=(100,100,100))
        graph_view.setCentralItem(graph_layout)
        # Mel filterbank plot
        fft_plot = graph_layout.addPlot(title='Filterbank Output', colspan=3)
        fft_plot.setRange(yRange=[-0.1, 1.2])
        fft_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
        x_data = np.array(range(1, config.settings["configuration"]["N_FFT_BINS"] + 1))
        self.mel_curve = pg.PlotCurveItem()
        self.mel_curve.setData(x=x_data, y=x_data*0)
        fft_plot.addItem(self.mel_curve)
        # Visualization plot
        graph_layout.nextRow()
        led_plot = graph_layout.addPlot(title='Visualization Output', colspan=3)
        led_plot.setRange(yRange=[-5, 260])
        led_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
        # Pen for each of the color channel curves
        r_pen = pg.mkPen((255, 30, 30, 200), width=4)
        g_pen = pg.mkPen((30, 255, 30, 200), width=4)
        b_pen = pg.mkPen((30, 30, 255, 200), width=4)
        # Color channel curves
        self.r_curve = pg.PlotCurveItem(pen=r_pen)
        self.g_curve = pg.PlotCurveItem(pen=g_pen)
        self.b_curve = pg.PlotCurveItem(pen=b_pen)
        # Define x data
        x_data = np.array(range(1, config.settings["configuration"]["N_PIXELS"] + 1))
        self.r_curve.setData(x=x_data, y=x_data*0)
        self.g_curve.setData(x=x_data, y=x_data*0)
        self.b_curve.setData(x=x_data, y=x_data*0)
        # Add curves to plot
        led_plot.addItem(self.r_curve)
        led_plot.addItem(self.g_curve)
        led_plot.addItem(self.b_curve)

        # ================================================= Set up button layout
        label_reactive = QLabel("Audio Reactive Effects")
        label_non_reactive = QLabel("Non Reactive Effects")
        reactive_button_grid = QGridLayout()
        non_reactive_button_grid = QGridLayout()        
        buttons = {}
        connecting_funcs = {}
        grid_width = 4
        i = 0
        j = 0
        k = 0
        l = 0
        # Dynamically layout reactive_buttons and connect them to the visualisation effects
        def connect_generator(effect):
            def func():
                visualizer.current_effect = effect
                buttons[effect].setDown(True)
            func.__name__ = effect
            return func
        # Where the magic happens
        for effect in visualizer.effects:
            if not effect in visualizer.non_reactive_effects:
                connecting_funcs[effect] = connect_generator(effect)
                buttons[effect] = QPushButton(effect)
                buttons[effect].clicked.connect(connecting_funcs[effect])
                reactive_button_grid.addWidget(buttons[effect], j, i)
                i += 1
                if i % grid_width == 0:
                    i = 0
                    j += 1
            else:
                connecting_funcs[effect] = connect_generator(effect)
                buttons[effect] = QPushButton(effect)
                buttons[effect].clicked.connect(connecting_funcs[effect])
                non_reactive_button_grid.addWidget(buttons[effect], l, k)
                k += 1
                if k % grid_width == 0:
                    k = 0
                    l += 1
                
        # ============================================== Set up frequency slider
        # Frequency range label
        label_slider = QLabel("Frequency Range")
        # Frequency slider
        def freq_slider_change(tick):
            minf = freq_slider.tickValue(0)**2.0 * (config.settings["configuration"]["MIC_RATE"] / 2.0)
            maxf = freq_slider.tickValue(1)**2.0 * (config.settings["configuration"]["MIC_RATE"] / 2.0)
            t = 'Frequency range: {:.0f} - {:.0f} Hz'.format(minf, maxf)
            freq_label.setText(t)
            config.settings["configuration"]["MIN_FREQUENCY"] = minf
            config.settings["configuration"]["MAX_FREQUENCY"] = maxf
            dsp.create_mel_bank()
        def set_freq_min():
            config.settings["configuration"]["MIN_FREQUENCY"] = freq_slider.start()
            dsp.create_mel_bank()
        def set_freq_max():
            config.settings["configuration"]["MAX_FREQUENCY"] = freq_slider.end()
            dsp.create_mel_bank()
        freq_slider = QRangeSlider()
        freq_slider.show()
        freq_slider.setMin(0)
        freq_slider.setMax(20000)
        freq_slider.setRange(config.settings["configuration"]["MIN_FREQUENCY"], config.settings["configuration"]["MAX_FREQUENCY"])
        freq_slider.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
        freq_slider.setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')
        freq_slider.setDrawValues(True)
        freq_slider.endValueChanged.connect(set_freq_max)
        freq_slider.startValueChanged.connect(set_freq_min)
        freq_slider.setStyleSheet("""
        QRangeSlider * {
            border: 0px;
            padding: 0px;
        }
        QRangeSlider > QSplitter::handle {
            background: #fff;
        }
        QRangeSlider > QSplitter::handle:vertical {
            height: 3px;
        }
        QRangeSlider > QSplitter::handle:pressed {
            background: #ca5;
        }
        """)

        # ============================================ Set up option tabs layout
        label_options = QLabel("Effect Options")
        opts_tabs = QTabWidget()
        # Dynamically set up tabs
        tabs = {}
        grid_layouts = {}
        self.grid_layout_widgets = {}
        options = visualizer.effect_opts.keys()
        for effect in visualizer.effects:
            # Make the tab
            self.grid_layout_widgets[effect] = {}
            tabs[effect] = QWidget()
            grid_layouts[effect] = QGridLayout()
            tabs[effect].setLayout(grid_layouts[effect])
            opts_tabs.addTab(tabs[effect],effect)
            # These functions make functions for the dynamic ui generation
            # YOU WANT-A DYNAMIC I GIVE-A YOU DYNAMIC!
            def gen_slider_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].value()
                return func
            def gen_float_slider_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].slider_value
                return func
            def gen_combobox_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].currentText()
                return func
            def gen_checkbox_valuechanger(effect, key):
                def func():
                    visualizer.effect_opts[effect][key] = self.grid_layout_widgets[effect][key].isChecked()
                return func
            # Dynamically generate ui for settings
            if effect in visualizer.dynamic_effects_config.settings["configuration"]["config:"]
                i = 0
                connecting_funcs[effect] = {}
                for key, label, ui_element, *opts in visualizer.dynamic_effects_config.settings["configuration"]["config[effect"]]:
                    if opts: # neatest way  ^^^^^ i could think of to unpack and handle an unknown number of opts (if any)
                        opts = opts[0]
                    if ui_element == "slider":
                        connecting_funcs[effect][key] = gen_slider_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QSlider(Qt.Horizontal)
                        self.grid_layout_widgets[effect][key].setMinimum(opts[0])
                        self.grid_layout_widgets[effect][key].setMaximum(opts[1])
                        self.grid_layout_widgets[effect][key].setValue(visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].valueChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "float_slider":
                        connecting_funcs[effect][key] = gen_float_slider_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QFloatSlider(*opts, visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].setValue(visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].valueChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "dropdown":
                        connecting_funcs[effect][key] = gen_combobox_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QComboBox()
                        self.grid_layout_widgets[effect][key].addItems(opts)
                        self.grid_layout_widgets[effect][key].currentIndexChanged.connect(
                                connecting_funcs[effect][key])
                    elif ui_element == "checkbox":
                        connecting_funcs[effect][key] = gen_checkbox_valuechanger(effect, key)
                        self.grid_layout_widgets[effect][key] = QCheckBox()
                        self.grid_layout_widgets[effect][key].setCheckState(visualizer.effect_opts[effect][key])
                        self.grid_layout_widgets[effect][key].stateChanged.connect(
                                connecting_funcs[effect][key])
                    grid_layouts[effect].addWidget(QLabel(label),i,0)
                    grid_layouts[effect].addWidget(self.grid_layout_widgets[effect][key],i,1)
                    i += 1    
                #visualizer.effect_settings[effect]
            else:
                grid_layouts[effect].addWidget(QLabel("No customisable options for this effect :("),0,0)
                
        
        
        # ============================================= Add layouts into wrapper
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(wrapper)
        wrapper.addLayout(labels_layout)
        wrapper.addWidget(graph_view)
        wrapper.addWidget(label_reactive)
        wrapper.addLayout(reactive_button_grid)
        wrapper.addWidget(label_non_reactive)
        wrapper.addLayout(non_reactive_button_grid)
        wrapper.addWidget(label_slider)
        wrapper.addWidget(freq_slider)
        wrapper.addWidget(label_options)
        wrapper.addWidget(opts_tabs)
        #self.show()
