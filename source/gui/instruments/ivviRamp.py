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
from time import sleep, perf_counter


# %% Main class


class ivviRamp(QtWidgets.QMainWindow):

    def __init__(self, rampdict, parent=None):
        """ Contstructs a simple viewer for Qcodes data.

        Args:
            data_directory (string or None): The directory to scan for experiments.
            default_parameter (string): A name of default parameter to plot.
            extensions (list): A list with the data file extensions to filter.
            verbose (int): The logging verbosity level.
        """
        super(ivviRamp, self).__init__(parent)


        self.main=parent
        self._timer: Optional[QCodesTimer] = None


        self.rampdict=rampdict

## ------------- DACs Layout
        vertLayout = QtWidgets.QVBoxLayout()

        dacsLayout = []

        self.dacsLabel=[]
        self.delayDAC=[]
        self.stepDAC=[]
        self.setDAC=[]
        self.getDAC=[]

        for kk in range(16):
          dacsLayout.append(QtWidgets.QHBoxLayout())

          self.dacsLabel.append(QtWidgets.QLabel())
          self.dacsLabel[kk].setText('DAC '+ str(kk+1))

          self.delayDAC.append(QtWidgets.QLineEdit())
          self.delayDAC[kk].setText(str(rampdict['dac'+str(kk+1)][0]))

          self.stepDAC.append(QtWidgets.QLineEdit())
          self.stepDAC[kk].setText(str(rampdict['dac'+str(kk+1)][1]))

          self.setDAC.append(QtWidgets.QPushButton())
          self.setDAC[kk].setText('Set')
          
          self.getDAC.append(QtWidgets.QPushButton())
          self.getDAC[kk].setText('Get')

          dacsLayout[kk].addWidget(self.dacsLabel[kk])
          dacsLayout[kk].addWidget(self.delayDAC[kk])
          dacsLayout[kk].addWidget(self.stepDAC[kk])
          dacsLayout[kk].addWidget(self.setDAC[kk])
          dacsLayout[kk].addWidget(self.getDAC[kk])

          vertLayout.addItem(dacsLayout[kk])

        self.setDAC[0].clicked.connect(lambda: self.set_dac(0))
        self.getDAC[0].clicked.connect(lambda: self.get_dac(0))
        self.setDAC[1].clicked.connect(lambda: self.set_dac(1))
        self.getDAC[1].clicked.connect(lambda: self.get_dac(1))
        self.setDAC[2].clicked.connect(lambda: self.set_dac(2))
        self.getDAC[2].clicked.connect(lambda: self.get_dac(2))
        self.setDAC[3].clicked.connect(lambda: self.set_dac(3))
        self.getDAC[3].clicked.connect(lambda: self.get_dac(3))
        self.setDAC[4].clicked.connect(lambda: self.set_dac(4))
        self.getDAC[4].clicked.connect(lambda: self.get_dac(4))
        self.setDAC[5].clicked.connect(lambda: self.set_dac(5))
        self.getDAC[5].clicked.connect(lambda: self.get_dac(5))
        self.setDAC[6].clicked.connect(lambda: self.set_dac(6))
        self.getDAC[6].clicked.connect(lambda: self.get_dac(6))
        self.setDAC[7].clicked.connect(lambda: self.set_dac(7))
        self.getDAC[7].clicked.connect(lambda: self.get_dac(7))
        self.setDAC[8].clicked.connect(lambda: self.set_dac(8))
        self.getDAC[8].clicked.connect(lambda: self.get_dac(8))
        self.setDAC[9].clicked.connect(lambda: self.set_dac(9))
        self.getDAC[9].clicked.connect(lambda: self.get_dac(9))
        self.setDAC[10].clicked.connect(lambda: self.set_dac(10))
        self.getDAC[10].clicked.connect(lambda: self.get_dac(10))
        self.setDAC[11].clicked.connect(lambda: self.set_dac(11))
        self.getDAC[11].clicked.connect(lambda: self.get_dac(11))
        self.setDAC[12].clicked.connect(lambda: self.set_dac(12))
        self.getDAC[12].clicked.connect(lambda: self.get_dac(12))
        self.setDAC[13].clicked.connect(lambda: self.set_dac(13))
        self.getDAC[13].clicked.connect(lambda: self.get_dac(13))
        self.setDAC[14].clicked.connect(lambda: self.set_dac(14))
        self.getDAC[14].clicked.connect(lambda: self.get_dac(14))
        self.setDAC[15].clicked.connect(lambda: self.set_dac(15))
        self.getDAC[15].clicked.connect(lambda: self.get_dac(15))


        self.GetAll=QtWidgets.QPushButton()
        self.GetAll.setText('Get all')
        self.GetAll.clicked.connect(self.get_all_dacs)

        vertLayout.addWidget(self.GetAll)


        widget = QtWidgets.QWidget()
        widget.setLayout(vertLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('IVVI DAC ramp rates')
        self.setGeometry(1000, 30, 100, 400)

        self.get_all_dacs()
        self.show()


## -------------- GUI functions 


    def get_dac(self,dac_number):
      delay_dac=getattr(self.main.main.station.ivvi,'dac'+str(dac_number+1)).inter_delay #getattr(self.main.station,'ivvi')._get_dac(dac_number+1) # change for stored component name 
      step_dac= getattr(self.main.main.station.ivvi,'dac'+str(dac_number+1)).step
      self.stepDAC[dac_number].setText(str(step_dac))
      self.delayDAC[dac_number].setText(str(delay_dac))

      self.rampdict['dac'+str(dac_number+1)]=[delay_dac,step_dac]

    def set_dac(self,dac_number,rate=None):

      val_delay=float(self.delayDAC[dac_number].text())
      val_step=float(self.stepDAC[dac_number].text())

      setattr(getattr(self.main.main.station.ivvi,'dac'+str(dac_number+1)),'inter_delay',val_delay)
      setattr(getattr(self.main.main.station.ivvi,'dac'+str(dac_number+1)),'step',val_step)

      self.rampdict['dac'+str(dac_number+1)]=[val_delay,val_step]


    def get_all_dacs(self):
      for indb in range(16):
        self.get_dac(indb)
