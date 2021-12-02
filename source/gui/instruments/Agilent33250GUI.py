# %% Load packages

import argparse
import logging
import os

import pyqtgraph as pg
import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
from qtpy.QtWidgets import QFileDialog, QWidget

import qcodes
from qcodes.plots.pyqtgraph import QtPlot

import numpy as np
from time import sleep




# %% Main class


class Agilent33250GUI(QtWidgets.QMainWindow):

    def __init__(self, instr_name, parent=None):
        """ Contstructs a simple viewer for Qcodes data.

        Args:
            data_directory (string or None): The directory to scan for experiments.
            default_parameter (string): A name of default parameter to plot.
            extensions (list): A list with the data file extensions to filter.
            verbose (int): The logging verbosity level.
        """

        super(Agilent33250GUI, self).__init__(parent)


        self.main=parent
        self._timer: Optional[QCodesTimer] = None

        self.instr_name=instr_name


        vertLayout = QtWidgets.QVBoxLayout()

        outchLine = QtWidgets.QHBoxLayout()

        boxwidth=120

        self.channelLabel=QtWidgets.QLabel()
        self.channelLabel.setText('Output channel: ')

        self.channelVal=QtWidgets.QComboBox()
        self.channelVal.addItem('1')
        self.channelVal.setFixedWidth(boxwidth)
        self.channelVal.currentIndexChanged.connect(self.toggleset)

        outchLine.addWidget(self.channelLabel)
        outchLine.addWidget(self.channelVal)

        syncLine = QtWidgets.QHBoxLayout()

        self.syncLabel=QtWidgets.QLabel()
        self.syncLabel.setText('Sync channel: ')

        self.syncVal=QtWidgets.QComboBox()
        self.syncVal.addItem('ON')
        self.syncVal.addItem('OFF')
        self.syncVal.setFixedWidth(boxwidth)        
        self.syncVal.currentIndexChanged.connect(self.toggleset)

        syncLine.addWidget(self.syncLabel)
        syncLine.addWidget(self.syncVal)

        triggerLayout = QtWidgets.QHBoxLayout()
        triggerLine = QtWidgets.QLabel()
        triggerLine.setText('Trigger settings')
        triggerLayout.addWidget(triggerLine)

        trigsourceLine = QtWidgets.QHBoxLayout()

        self.trigsourceLabel=QtWidgets.QLabel()
        self.trigsourceLabel.setText('Trigger source: ')

        self.trigsourceVal=QtWidgets.QComboBox()
        self.trigsourceVal.addItem('IMM')
        self.trigsourceVal.addItem('EXT')
        self.trigsourceVal.addItem('BUS')
        self.trigsourceVal.setFixedWidth(boxwidth)        
        self.trigsourceVal.currentIndexChanged.connect(self.toggleset)

        trigsourceLine.addWidget(self.trigsourceLabel)
        trigsourceLine.addWidget(self.trigsourceVal)

        trigslopeLine = QtWidgets.QHBoxLayout()

        self.trigslopeLabel=QtWidgets.QLabel()
        self.trigslopeLabel.setText('Trigger slope: ')

        self.trigslopeVal=QtWidgets.QComboBox()
        self.trigslopeVal.addItem('POS')
        self.trigslopeVal.addItem('NEG')
        self.trigslopeVal.setFixedWidth(boxwidth)        
        self.trigslopeVal.currentIndexChanged.connect(self.toggleset)

        trigslopeLine.addWidget(self.trigslopeLabel)
        trigslopeLine.addWidget(self.trigslopeVal)        

        outputLayout = QtWidgets.QHBoxLayout()
        outputLine=QtWidgets.QLabel()
        outputLine.setText('Output settings')
        outputLayout.addWidget(outputLine)

        funcLine = QtWidgets.QHBoxLayout()

        self.funcLabel=QtWidgets.QLabel()
        self.funcLabel.setText('Function type: ')

        self.funcVal=QtWidgets.QComboBox()
        self.funcVal.addItem('SIN')
        self.funcVal.addItem('SQU')
        self.funcVal.addItem('TRI')
        self.funcVal.addItem('PULS')
        self.funcVal.addItem('PRBS')
        self.funcVal.addItem('NOIS')
        self.funcVal.addItem('ARB')
        self.funcVal.addItem('DC')
        self.funcVal.setFixedWidth(boxwidth)        
        self.funcVal.currentIndexChanged.connect(self.toggleset)

        funcLine.addWidget(self.funcLabel)
        funcLine.addWidget(self.funcVal)

        freqmodeLine = QtWidgets.QHBoxLayout()

        self.freqmodeLabel=QtWidgets.QLabel()
        self.freqmodeLabel.setText('Frequency mode: ')

        self.freqmodeVal=QtWidgets.QComboBox()
        self.freqmodeVal.addItem('CW')
        self.freqmodeVal.addItem('LIST')
        self.freqmodeVal.addItem('SWEEP')
        self.freqmodeVal.addItem('FIXED')
        self.freqmodeVal.setFixedWidth(boxwidth)        
        self.freqmodeVal.currentIndexChanged.connect(self.toggleset)

        freqmodeLine.addWidget(self.freqmodeLabel)
        freqmodeLine.addWidget(self.freqmodeVal)              

        freqLine = QtWidgets.QHBoxLayout()

        self.freqLabel=QtWidgets.QLabel()
        self.freqLabel.setText('Frequency: ')

        self.freqVal=QtWidgets.QLineEdit()
        self.freqVal.setText('0.0')
        self.freqVal.setFixedWidth(boxwidth)        
        self.freqVal.textChanged.connect(self.toggleset)

        freqLine.addWidget(self.freqLabel)
        freqLine.addWidget(self.freqVal)

        phaseLine = QtWidgets.QHBoxLayout()

        self.phaseLabel=QtWidgets.QLabel()
        self.phaseLabel.setText('Phase: ')

        self.phaseVal=QtWidgets.QLineEdit()
        self.phaseVal.setText('0.0')
        self.phaseVal.setFixedWidth(boxwidth)        
        self.phaseVal.textChanged.connect(self.toggleset)

        phaseLine.addWidget(self.phaseLabel)
        phaseLine.addWidget(self.phaseVal)

        ampLine = QtWidgets.QHBoxLayout()

        self.ampLabel=QtWidgets.QLabel()
        self.ampLabel.setText('Amplitude: ')

        self.ampVal=QtWidgets.QLineEdit()
        self.ampVal.setText('0.0')
        self.ampVal.setFixedWidth(boxwidth)        
        self.ampVal.textChanged.connect(self.toggleset)

        ampLine.addWidget(self.ampLabel)
        ampLine.addWidget(self.ampVal)

        ampunitLine = QtWidgets.QHBoxLayout()

        self.ampunitLabel=QtWidgets.QLabel()
        self.ampunitLabel.setText('Amplitude unit: ')

        self.ampunitVal=QtWidgets.QComboBox()
        self.ampunitVal.addItem('VPP')
        self.ampunitVal.addItem('VRMS')
        self.ampunitVal.addItem('DBM')
        self.ampunitVal.setFixedWidth(boxwidth)        
        self.ampunitVal.currentIndexChanged.connect(self.toggleset)

        ampunitLine.addWidget(self.ampunitLabel)
        ampunitLine.addWidget(self.ampunitVal)

        dutyLine = QtWidgets.QHBoxLayout()

        self.dutyLabel=QtWidgets.QLabel()
        self.dutyLabel.setText('Duty cycle: ')

        self.dutyVal=QtWidgets.QLineEdit()
        self.dutyVal.setText('50.0')
        self.dutyVal.setFixedWidth(boxwidth)        
        self.dutyVal.textChanged.connect(self.toggleset)

        dutyLine.addWidget(self.dutyLabel)
        dutyLine.addWidget(self.dutyVal)

        offsetLine = QtWidgets.QHBoxLayout()

        self.offsetLabel=QtWidgets.QLabel()
        self.offsetLabel.setText('Offset: ')

        self.offsetVal=QtWidgets.QLineEdit()
        self.offsetVal.setText('0.0')
        self.offsetVal.setFixedWidth(boxwidth)        
        self.offsetVal.textChanged.connect(self.toggleset)

        offsetLine.addWidget(self.offsetLabel)
        offsetLine.addWidget(self.offsetVal)

        outpolLine = QtWidgets.QHBoxLayout()

        self.outpolLabel=QtWidgets.QLabel()
        self.outpolLabel.setText('Output polarity: ')

        self.outpolVal=QtWidgets.QComboBox()
        self.outpolVal.addItem('NORM')
        self.outpolVal.addItem('INV')
        self.outpolVal.setFixedWidth(boxwidth)        
        self.outpolVal.currentIndexChanged.connect(self.toggleset)

        outpolLine.addWidget(self.outpolLabel)
        outpolLine.addWidget(self.outpolVal)

        burstLayout = QtWidgets.QHBoxLayout()
        burstLine = QtWidgets.QLabel()
        burstLine.setText('Burst settings')
        burstLayout.addWidget(burstLine)

        burstmodeLine = QtWidgets.QHBoxLayout()

        self.burstmodeLabel=QtWidgets.QLabel()
        self.burstmodeLabel.setText('Burst mode: ')

        self.burstmodeVal=QtWidgets.QComboBox()
        self.burstmodeVal.addItem('N Cycle')
        self.burstmodeVal.addItem('Gated')
        self.burstmodeVal.setFixedWidth(boxwidth)        
        self.burstmodeVal.currentIndexChanged.connect(self.toggleset)

        burstmodeLine.addWidget(self.burstmodeLabel)
        burstmodeLine.addWidget(self.burstmodeVal)
        
        burstcyclesLine = QtWidgets.QHBoxLayout()

        self.burstcyclesLabel=QtWidgets.QLabel()
        self.burstcyclesLabel.setText('Burst cycles: ')

        self.burstcyclesVal=QtWidgets.QLineEdit()
        self.burstcyclesVal.setText('INF')
        self.burstcyclesVal.setFixedWidth(boxwidth)        
        self.burstcyclesVal.textChanged.connect(self.toggleset)

        burstcyclesLine.addWidget(self.burstcyclesLabel)
        burstcyclesLine.addWidget(self.burstcyclesVal)

        outstatusLayout = QtWidgets.QHBoxLayout()
        outstatusLine = QtWidgets.QLabel()
        outstatusLine.setText('Output status')
        outstatusLayout.addWidget(outstatusLine)

        outLine = QtWidgets.QHBoxLayout()

        self.outLabel=QtWidgets.QLabel()
        self.outLabel.setText('Output: ')

        self.outVal=QtWidgets.QComboBox()
        self.outVal.addItem('ON')
        self.outVal.addItem('OFF')
        self.outVal.setFixedWidth(boxwidth)        
        self.outVal.currentIndexChanged.connect(self.toggleset)

        outLine.addWidget(self.outLabel)
        outLine.addWidget(self.outVal)

        burstLine = QtWidgets.QHBoxLayout()

        self.burstLabel=QtWidgets.QLabel()
        self.burstLabel.setText('Burst: ')

        self.burstVal=QtWidgets.QComboBox()
        self.burstVal.addItem('ON')
        self.burstVal.addItem('OFF')
        self.burstVal.setFixedWidth(boxwidth)        
        self.burstVal.currentIndexChanged.connect(self.toggleset)

        burstLine.addWidget(self.burstLabel)
        burstLine.addWidget(self.burstVal)


        self.setButton = QtWidgets.QPushButton()
        self.setButton.setText('Set setttings')
        
        self.setButton.clicked.connect(self.setsettings)

        self.getButton = QtWidgets.QPushButton()
        self.getButton.setText('Get settings')
        self.getButton.clicked.connect(self.getsettings)

        self.trigButton = QtWidgets.QPushButton()
        self.trigButton.setText('Force Trigger')
        self.trigButton.clicked.connect(self.forcetrigger)

        vertLayout.addItem(outchLine)
        vertLayout.addItem(triggerLayout)
        vertLayout.addItem(trigsourceLine)
        vertLayout.addItem(trigslopeLine)
        vertLayout.addItem(outputLayout)
        vertLayout.addItem(funcLine)
        vertLayout.addItem(freqmodeLine)
        vertLayout.addItem(freqLine)
        vertLayout.addItem(phaseLine)
        vertLayout.addItem(ampLine)
        vertLayout.addItem(ampunitLine)
        vertLayout.addItem(dutyLine)
        vertLayout.addItem(offsetLine)
        vertLayout.addItem(outpolLine)
        vertLayout.addItem(burstLayout)
        vertLayout.addItem(burstmodeLine)
        vertLayout.addItem(burstcyclesLine)
        vertLayout.addItem(outstatusLayout)
        vertLayout.addItem(syncLine)
        vertLayout.addItem(outLine)
        vertLayout.addItem(burstLine)

        vertLayout.addWidget(self.getButton)
        vertLayout.addWidget(self.setButton)
        vertLayout.addWidget(self.trigButton)


        widget = QtWidgets.QWidget()
        widget.setLayout(vertLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Agilent 33250A GUI')
        self.setGeometry(1000, 30, 200, 700)

        self.getsettings()
        self.setButton.setEnabled(False)
        self.show()




## -------------- GUI functions 

    def toggleset(self):

      self.setButton.setEnabled(True)

    def forcetrigger(self):

        self.main.station[self.instr_name].force_trigger()

    def setsettings(self):

      instr_channel = getattr(getattr(self.main.station,self.instr_name),'ch'+self.channelVal.currentText())
      
      print(self.trigsourceVal.currentText())
      instr_channel.trigger_source(self.trigsourceVal.currentText())
      instr_channel.trigger_slope(self.trigslopeVal.currentText())
      instr_channel.function_type(self.funcVal.currentText())
      instr_channel.frequency_mode(self.freqmodeVal.currentText())
      instr_channel.frequency(float(self.freqVal.text()))
      instr_channel.phase(float(self.phaseVal.text()))
      instr_channel.amplitude_unit(self.ampunitVal.currentText())
      instr_channel.amplitude(float(self.ampVal.text()))
      instr_channel.duty_cycle(float(self.dutyVal.text()))
      instr_channel.offset(float(self.offsetVal.text()))
      instr_channel.output_polarity(self.outpolVal.currentText())
      instr_channel.burst_mode(self.burstmodeVal.currentText())
      instr_channel.burst_ncycles(self.burstcyclesVal.text())
      instr_channel.output(self.outVal.currentText())
      instr_channel.burst_state(self.burstVal.currentText())

      getattr(self.main.station,self.instr_name).sync.output(self.syncVal.currentText())

      self.setButton.setEnabled(False)

    def getsettings(self):

      instr_channel = getattr(getattr(self.main.station,self.instr_name),'ch'+self.channelVal.currentText())
      
      newval = instr_channel.trigger_source()
      print(newval)
      self.trigsourceVal.setCurrentIndex(self.trigsourceVal.findText(newval))

      newval = instr_channel.trigger_slope()
      self.trigslopeVal.setCurrentIndex(self.trigslopeVal.findText(newval))
      
      newval = instr_channel.function_type()
      self.funcVal.setCurrentIndex(self.funcVal.findText(newval))

      newval = instr_channel.frequency_mode()
      self.freqmodeVal.setCurrentIndex(self.freqmodeVal.findText(newval))

      newval = instr_channel.frequency()
      self.freqVal.setText(str(newval).upper())

      newval = instr_channel.phase()
      self.phaseVal.setText(str(newval).upper())

      newval = instr_channel.amplitude_unit()
      self.ampunitVal.setCurrentIndex(self.ampunitVal.findText(newval))

      newval = instr_channel.amplitude()
      self.ampVal.setText(str(newval).upper())

      newval = instr_channel.duty_cycle()
      self.dutyVal.setText(str(newval))

      newval = instr_channel.offset()
      self.offsetVal.setText(str(newval).upper())

      newval = instr_channel.output_polarity()
      self.outpolVal.setCurrentIndex(self.outpolVal.findText(newval))

      newval = instr_channel.burst_mode()
      self.burstmodeVal.setCurrentIndex(self.burstmodeVal.findText(newval))
      
      newval = instr_channel.burst_ncycles()
      self.burstcyclesVal.setText(str(newval).upper())

      newval = instr_channel.output()
      self.outVal.setCurrentIndex(self.outVal.findText(newval))
      
      newval = instr_channel.burst_state()
      self.burstVal.setCurrentIndex(self.burstVal.findText(newval))

