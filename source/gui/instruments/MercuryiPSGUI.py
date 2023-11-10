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



# %% Main class


class MercuryiPSGUI(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        """ Contstructs a simple viewer for Qcodes data.

        Args:
            data_directory (string or None): The directory to scan for experiments.
            default_parameter (string): A name of default parameter to plot.
            extensions (list): A list with the data file extensions to filter.
            verbose (int): The logging verbosity level.
        """
        super(MercuryiPSGUI, self).__init__(parent)


        self.main=parent
        self._timer: Optional[QCodesTimer] = None


## ------------- Fields

        vertLayout = QtWidgets.QVBoxLayout()


        self.Bx_label=QtWidgets.QLabel()
        self.Bx_label.setText('GRPX')
        vertLayout.addWidget(self.Bx_label)

        Bx_target_lay=QtWidgets.QHBoxLayout()
        
        self.Bx_target_text=QtWidgets.QLineEdit()
        self.Bx_target_text.setText('0.0')
        Bx_target_lay.addWidget(self.Bx_target_text)  
        
        self.Bx_target_set=QtWidgets.QPushButton()
        self.Bx_target_set.setText('Set')
        self.Bx_target_set.clicked.connect(lambda: self.set_target('GRPX'))
        Bx_target_lay.addWidget(self.Bx_target_set)

        
        self.Bx_target_get=QtWidgets.QPushButton()
        self.Bx_target_get.setText('Get')
        self.Bx_target_get.clicked.connect(lambda: self.get_target('GRPX'))
        Bx_target_lay.addWidget(self.Bx_target_get)

        vertLayout.addItem(Bx_target_lay)

        Bx_actual_lay=QtWidgets.QHBoxLayout()
        
        self.Bx_actual_text=QtWidgets.QLineEdit()
        self.Bx_actual_text.setText('0.0')
        Bx_actual_lay.addWidget(self.Bx_actual_text)  
        
        self.Bx_actual_get=QtWidgets.QPushButton()
        self.Bx_actual_get.setText('Get')
        self.Bx_actual_get.clicked.connect(lambda: self.get_field('GRPX'))
        Bx_actual_lay.addWidget(self.Bx_actual_get)

        vertLayout.addItem(Bx_actual_lay)

        Bx_current_lay=QtWidgets.QHBoxLayout()
        
        self.Bx_current_text=QtWidgets.QLineEdit()
        self.Bx_current_text.setText('0.0')
        Bx_current_lay.addWidget(self.Bx_current_text)  
        
        self.Bx_current_get=QtWidgets.QPushButton()
        self.Bx_current_get.setText('Get')
        self.Bx_current_get.clicked.connect(lambda: self.get_current('GRPX'))
        Bx_current_lay.addWidget(self.Bx_current_get)

        vertLayout.addItem(Bx_current_lay)

        persistent_x_lay=QtWidgets.QHBoxLayout()

        self.persistent_x_label=QtWidgets.QLabel()
        self.persistent_x_label.setText('Persistent mode')
        persistent_x_lay.addWidget(self.persistent_x_label)

        self.persistent_x_on_button=QtWidgets.QPushButton()
        self.persistent_x_on_button.setText('ON')
        self.persistent_x_on_button.clicked.connect(lambda: self.persistent_on('GRPX','on'))
        persistent_x_lay.addWidget(self.persistent_x_on_button)

        self.persistent_x_off_button=QtWidgets.QPushButton()
        self.persistent_x_off_button.setText('OFF')
        self.persistent_x_off_button.clicked.connect(lambda: self.persistent_off('GRPX','off'))
        persistent_x_lay.addWidget(self.persistent_x_off_button)

        vertLayout.addItem(persistent_x_lay)

        ## y 

        self.By_label=QtWidgets.QLabel()
        self.By_label.setText('GRPY')
        vertLayout.addWidget(self.By_label)
        
        By_target_lay=QtWidgets.QHBoxLayout()
        
        self.By_target_text=QtWidgets.QLineEdit()
        self.By_target_text.setText('0.0')
        By_target_lay.addWidget(self.By_target_text)  
        
        self.By_target_set=QtWidgets.QPushButton()
        self.By_target_set.setText('Set')
        self.By_target_set.clicked.connect(lambda: self.set_target('GRPY'))
        By_target_lay.addWidget(self.By_target_set)
        
        self.By_target_get=QtWidgets.QPushButton()
        self.By_target_get.setText('Get')
        self.By_target_get.clicked.connect(lambda: self.get_target('GRPY'))
        By_target_lay.addWidget(self.By_target_get)

        vertLayout.addItem(By_target_lay)

        By_actual_lay=QtWidgets.QHBoxLayout()
        
        self.By_actual_text=QtWidgets.QLineEdit()
        self.By_actual_text.setText('0.0')
        By_actual_lay.addWidget(self.By_actual_text)
        
        self.By_actual_get=QtWidgets.QPushButton()
        self.By_actual_get.setText('Get')
        self.By_actual_get.clicked.connect(lambda: self.get_field('GRPY'))
        By_actual_lay.addWidget(self.By_actual_get)

        vertLayout.addItem(By_actual_lay)

        By_current_lay=QtWidgets.QHBoxLayout()
        
        self.By_current_text=QtWidgets.QLineEdit()
        self.By_current_text.setText('0.0')
        By_current_lay.addWidget(self.By_current_text)
        
        self.By_current_get=QtWidgets.QPushButton()
        self.By_current_get.setText('Get')
        self.By_current_get.clicked.connect(lambda: self.get_current('GRPY'))
        By_current_lay.addWidget(self.By_current_get)

        vertLayout.addItem(By_current_lay)

        persistent_y_lay=QtWidgets.QHBoxLayout()

        self.persistent_y_label=QtWidgets.QLabel()
        self.persistent_y_label.setText('Persistent mode')
        persistent_y_lay.addWidget(self.persistent_y_label)

        self.persistent_y_on_button=QtWidgets.QPushButton()
        self.persistent_y_on_button.setText('ON')
        self.persistent_y_on_button.clicked.connect(lambda: self.persistent_on('GRPY','on'))
        persistent_y_lay.addWidget(self.persistent_y_on_button)

        self.persistent_y_off_button=QtWidgets.QPushButton()
        self.persistent_y_off_button.setText('OFF')
        self.persistent_y_off_button.clicked.connect(lambda: self.persistent_off('GRPY','off'))
        persistent_y_lay.addWidget(self.persistent_y_off_button)

        vertLayout.addItem(persistent_y_lay)


        ## z

        self.Bz_label=QtWidgets.QLabel()
        self.Bz_label.setText('GRPZ')
        vertLayout.addWidget(self.Bz_label)

        Bz_target_lay=QtWidgets.QHBoxLayout()
        
        self.Bz_target_text=QtWidgets.QLineEdit()
        self.Bz_target_text.setText('0.0')
        Bz_target_lay.addWidget(self.Bz_target_text)
        
        self.Bz_target_set=QtWidgets.QPushButton()
        self.Bz_target_set.setText('Set')
        self.Bz_target_set.clicked.connect(lambda: self.set_target('GRPZ'))
        Bz_target_lay.addWidget(self.Bz_target_set)
        
        self.Bz_target_get=QtWidgets.QPushButton()
        self.Bz_target_get.setText('Get')
        self.Bz_target_get.clicked.connect(lambda: self.get_target('GRPZ'))
        Bz_target_lay.addWidget(self.Bz_target_get)

        vertLayout.addItem(Bz_target_lay)

        Bz_actual_lay=QtWidgets.QHBoxLayout()
        
        self.Bz_actual_text=QtWidgets.QLineEdit()
        self.Bz_actual_text.setText('0.0')
        Bz_actual_lay.addWidget(self.Bz_actual_text)
        
        self.Bz_actual_get=QtWidgets.QPushButton()
        self.Bz_actual_get.setText('Get')
        self.Bz_actual_get.clicked.connect(lambda: self.get_field('GRPZ'))
        Bz_actual_lay.addWidget(self.Bz_actual_get)

        vertLayout.addItem(Bz_actual_lay)

        Bz_current_lay=QtWidgets.QHBoxLayout()
        
        self.Bz_current_text=QtWidgets.QLineEdit()
        self.Bz_current_text.setText('0.0')
        Bz_current_lay.addWidget(self.Bz_current_text)
        
        self.Bz_current_get=QtWidgets.QPushButton()
        self.Bz_current_get.setText('Get')
        self.Bz_current_get.clicked.connect(lambda: self.get_current('GRPZ'))
        Bz_current_lay.addWidget(self.Bz_current_get)

        vertLayout.addItem(Bz_current_lay)

        persistent_z_lay=QtWidgets.QHBoxLayout()

        self.persistent_z_label=QtWidgets.QLabel()
        self.persistent_z_label.setText('Persistent mode')
        persistent_z_lay.addWidget(self.persistent_z_label)

        self.persistent_z_on_button=QtWidgets.QPushButton()
        self.persistent_z_on_button.setText('ON')
        self.persistent_z_on_button.clicked.connect(lambda: self.persistent_on('GRPZ','on'))
        persistent_z_lay.addWidget(self.persistent_z_on_button)

        self.persistent_z_off_button=QtWidgets.QPushButton()
        self.persistent_z_off_button.setText('OFF')
        self.persistent_z_off_button.clicked.connect(lambda: self.persistent_off('GRPZ','off'))
        persistent_z_lay.addWidget(self.persistent_z_off_button)

        vertLayout.addItem(persistent_z_lay)

        ## extra buttons

        self.ramp_button=QtWidgets.QPushButton()
        self.ramp_button.setText('Ramp to target field')
        self.ramp_button.clicked.connect(lambda: self.main.station['magnet'].GRPZ.ramp_to_target()) ## IMPORTANT: fix this for 3 axes!!!
        vertLayout.addWidget(self.ramp_button)

        heater_lay=QtWidgets.QHBoxLayout()

        self.heater_label=QtWidgets.QLabel()
        self.heater_label.setText('Switch heater')
        heater_lay.addWidget(self.heater_label)


        self.heater_on_button=QtWidgets.QPushButton()
        self.heater_on_button.setText('ON')
        self.heater_on_button.clicked.connect(lambda: self.heater_status('GRPZ','ON'))
        heater_lay.addWidget(self.heater_on_button)

        self.heater_off_button=QtWidgets.QPushButton()
        self.heater_off_button.setText('OFF')
        self.heater_off_button.clicked.connect(lambda: self.heater_status('GRPZ','OFF'))
        heater_lay.addWidget(self.heater_off_button)

        vertLayout.addItem(heater_lay)

        status_lay=QtWidgets.QHBoxLayout()

        self.status_text=QtWidgets.QLabel()
        self.status_text.setText('')
        status_lay.addWidget(self.status_text)

        self.status_button=QtWidgets.QPushButton()
        self.status_button.setText('Status')
        self.status_button.clicked.connect(lambda: self.get_status())
        status_lay.addWidget(self.status_button)

        vertLayout.addItem(status_lay)


        widget = QtWidgets.QWidget()
        widget.setLayout(vertLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Mercury iPS GUI')
        self.setGeometry(1000, 30, 300, 500)

        # self.updatecallback()
        self.show()

        self.get_target('GRPX')
        self.get_target('GRPY')
        self.get_target('GRPZ')

        self.get_field('GRPX')
        self.get_field('GRPY')
        self.get_field('GRPZ')

        self.get_heater()

## -------------- GUI functions 

    def get_target(self,psu):
      B_target = getattr(self.main.station['magnet'],psu).field_target.get()
      if psu=='GRPX':
        self.Bx_target_text.setText(str(B_target))
      elif psu=='GRPY':
        self.By_target_text.setText(str(B_target))
      elif psu=='GRPZ':
        self.Bz_target_text.setText(str(B_target))


    def set_target(self,psu):
      if psu=='GRPX':
        getattr(self.main.station['magnet'],psu).field_target.set(float(self.Bx_target_text.text()))
      elif psu=='GRPY':
        getattr(self.main.station['magnet'],psu).field_target.set(float(self.By_target_text.text()))
      elif psu=='GRPZ':
        getattr(self.main.station['magnet'],psu).field_target.set(float(self.Bz_target_text.text()))


    def get_field(self,psu):

      B_actual = getattr(self.main.station['magnet'],psu).field.get()
      if psu=='GRPX':
        self.Bx_actual_text.setText(str(B_actual))
      elif psu=='GRPY':
        self.By_actual_text.setText(str(B_actual))
      elif psu=='GRPZ':
        self.Bz_actual_text.setText(str(B_actual))

    def get_current(self,psu):
      
      Curr_actual = getattr(self.main.station['magnet'],psu).current.get()
      if psu=='GRPX':
        self.Bx_current_text.setText(str(Curr_actual))
      elif psu=='GRPY':
        self.By_current_text.setText(str(Curr_actual))
      elif psu=='GRPZ':
        self.Bz_current_text.setText(str(Curr_actual))

    def persistent_on(self,psu):
      print('Not implemented')

    def persistent_off(self,psu):
      print('Not implemented')

    def heater_status(self,psu,status):
      print(psu)
      print(status)
      getattr(self.main.station['magnet'],psu).switch_heater.get()
      getattr(self.main.station['magnet'],psu).switch_heater.set(status)
      self.get_heater()



    def get_heater(self):
      heater_status=self.main.station['magnet'].GRPZ.switch_heater.get()
      print(heater_status)
      if heater_status=='ON':
        self.heater_on_button.setEnabled(False)
        self.heater_off_button.setEnabled(True)
      elif heater_status=='OFF':
        self.heater_on_button.setEnabled(True)
        self.heater_off_button.setEnabled(False)



    def get_status(self):
      status_x=self.main.station['magnet'].GRPX.ramp_status()
      status_y=self.main.station['magnet'].GRPY.ramp_status()
      status_z=self.main.station['magnet'].GRPZ.ramp_status()

      self.status_text.setText('GRPX: '+status_x+' GRPY: '+status_y+' GRPZ: '+status_z)