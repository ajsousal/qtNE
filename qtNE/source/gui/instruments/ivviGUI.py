# %% Load packages

import argparse
import logging
import os

import pyqtgraph as pg
import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
from qtpy.QtWidgets import QFileDialog, QWidget

import qcodes
from qcodes_loop.plots.pyqtgraph import QtPlot

import numpy as np
from time import sleep, perf_counter

from source.gui.instruments import ivviRamp



# %% Main class


class IVVIGUI(QtWidgets.QMainWindow):


    def __init__(self, parent=None):
        """ Contstructs a simple viewer for Qcodes data.

        Args:
            data_directory (string or None): The directory to scan for experiments.
            default_parameter (string): A name of default parameter to plot.
            extensions (list): A list with the data file extensions to filter.
            verbose (int): The logging verbosity level.
        """
        super(IVVIGUI, self).__init__(parent)


        self.main=parent
        self._timer: Optional[QCodesTimer] = None


## ------------- DACs Layout
        vertLayout = QtWidgets.QVBoxLayout()

        dacsLayout = []

        self.dacsLabel=[]
        self.valDAC=[]
        self.setDAC=[]
        self.getDAC=[]

        for kk in range(16):
          dacsLayout.append(QtWidgets.QHBoxLayout())

          self.dacsLabel.append(QtWidgets.QLabel())
          self.dacsLabel[kk].setText('DAC '+ str(kk+1))

          self.valDAC.append(QtWidgets.QLineEdit())
          self.valDAC[kk].setText('0.0')
          # self.val_dac[kk]=float(self.valDAC[kk])

          self.setDAC.append(QtWidgets.QPushButton())
          self.setDAC[kk].setText('Set')
          # self.setDAC[kk].clicked.connect(lambda x=kk: self.set_dac(x))

          self.getDAC.append(QtWidgets.QPushButton())
          self.getDAC[kk].setText('Get')
          # self.getDAC[kk].clicked.connect(lambda x=kk: self.get_dac(x))




          dacsLayout[kk].addWidget(self.dacsLabel[kk])
          dacsLayout[kk].addWidget(self.valDAC[kk])
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


        polsLayout=[]

        self.polLabel=[]
        self.polDAC=[]
        self.setPOL=[]
        self.getPOL=[]

        for jj in range(4):
          polsLayout.append(QtWidgets.QHBoxLayout())

          self.polLabel.append(QtWidgets.QLabel())
          self.polLabel[jj].setText('POL '+ str(jj))

          self.polDAC.append(QtWidgets.QComboBox())
          self.polDAC[jj]

          self.setPOL.append(QtWidgets.QPushButton())
          self.setPOL[jj].setText('Set')

          self.getPOL.append(QtWidgets.QPushButton())
          self.getPOL[jj].setText('Get')

          polsLayout[jj].addWidget(self.polLabel[jj])
          polsLayout[jj].addWidget(self.polDAC[jj])
          polsLayout[jj].addWidget(self.setPOL[jj])
          polsLayout[jj].addWidget(self.getPOL[jj])


          vertLayout.addItem(polsLayout[jj])


        self.GetAll=QtWidgets.QPushButton()
        self.GetAll.setText('Get All DACs')
        self.GetAll.clicked.connect(self.get_all_dacs)

        self.SetZero=QtWidgets.QPushButton()
        self.SetZero.setText('Set DACs to zero')
        self.SetZero.clicked.connect(self.set_to_zero)

        self.RampRates=QtWidgets.QPushButton()
        self.RampRates.setText('DACs ramp rates')
        self.RampRates.clicked.connect(self.rampGUI)


        vertLayout.addWidget(self.RampRates)
        vertLayout.addWidget(self.GetAll)
        vertLayout.addWidget(self.SetZero)



        widget = QtWidgets.QWidget()
        widget.setLayout(vertLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('IVVI Rack GUI')
        self.setGeometry(1000, 30, 500, 900)


        rampdict=self.get_ramps()

        self.get_all_dacs()
        # self.updatecallback()
        self.show()




## -------------- GUI functions 


    def get_dac(self,dac_number):
      val_dac=getattr(self.main.station,'ivvi')._get_dac(dac_number+1) # change for stored component name 
      self.valDAC[dac_number].setText(str(val_dac))




    def set_dac(self,dac_number,rate=None):

      if rate is None:
        rate=100

      val_dac=float(self.valDAC[dac_number].text())
      self._set_stable(val_dac,dac_number,rate)




    def set_to_zero(self):
      for inda in range(16):
        self._set_stable(0,inda,100)
        self.valDAC[inda].setText(str(0.0))    
            
      self.get_all_dacs()




    def get_all_dacs(self):
      for indb in range(16):
        self.get_dac(indb)


    def get_ramps(self):
      rampdict={}
      for kk in range(16):
        delay = getattr(self.main.station.ivvi,'dac'+str(kk+1)).inter_delay
        step = getattr(self.main.station.ivvi,'dac'+str(kk+1)).step
        rampdict['dac'+str(kk+1)]=[delay,step]
      return rampdict

    def rampGUI(self):
      self.rampdict=self.get_ramps()
      self.rampgui=ivviRamp.ivviRamp(self.rampdict,self)
      self.rampgui.show()


    def _set_stable(self,value,dac_number,rate):
        
        getattr(self.main.station.ivvi,'dac'+str(dac_number+1)).set(value)
