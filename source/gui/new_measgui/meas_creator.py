# %% Load packages

import argparse
import logging
import os

import pyqtgraph as pg
import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
# from qtpy.QtWidgets import QFileDialog, QWidget

# import qcodes
# from qcodes.plots.pyqtgraph import QtPlot

import numpy as np
from time import sleep, perf_counter

import inspect
import importlib

# %% Main class


class MeasurementCreator(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        super(MeasurementCreator, self).__init__(parent)


        self.main=parent


## ------------- Fields

        horLayout= QtWidgets.QHBoxLayout()   
        
        instrpoolLayout = QtWidgets.QVBoxLayout()

        self.instrpool_label=QtWidgets.QLabel()
        self.instrpool_label.setText('Instrument Pool')
        self.instrpool_tree=QtWidgets.QTreeView()
        ## change tree behavior later 
        self.instrpool_tree.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.instrtree_model = QtGui.QStandardItemModel()
        self.instrpool_tree.setModel(self.instrtree_model)
        ##
        
        self.instrpool_tree.clicked.connect(lambda: self.check_item_for_buttons(self.instrpool_tree.currentIndex()))
        self.instrpool_tree.selectionModel().selectionChanged.connect(lambda: self.check_item_for_buttons(self.instrpool_tree.currentIndex()))
        
        
        instrpool_buttonsLayout = QtWidgets.QHBoxLayout()
        
        self.configInstr = QtWidgets.QPushButton()
        self.configInstr.setText('Config')
        self.configInstr.setEnabled(False)
        self.addInstr = QtWidgets.QPushButton()
        self.addInstr.setText('Add')
        self.addInstr.setEnabled(False)
        
        self.addInstr.clicked.connect(lambda: self.add_parameter(self.instrpool_tree.currentIndex().parent()))
        
        self.remInstr = QtWidgets.QPushButton()
        self.remInstr.setText('Remove')
        self.remInstr.setEnabled(False)
        self.editInstr = QtWidgets.QPushButton()
        self.editInstr.setText('Edit')
        self.editInstr.setEnabled(False)
        self.setVal = QtWidgets.QPushButton()
        self.setVal.setText('Set val.')
        self.setVal.setEnabled(False)
        self.getVal = QtWidgets.QPushButton()
        self.getVal.setText('Get val.')
        self.getVal.setEnabled(False)
        
        instrpool_buttonsLayout.addWidget(self.getVal)
        instrpool_buttonsLayout.addWidget(self.setVal)
        instrpool_buttonsLayout.addWidget(self.configInstr)
        instrpool_buttonsLayout.addWidget(self.addInstr)
        instrpool_buttonsLayout.addWidget(self.editInstr)
        instrpool_buttonsLayout.addWidget(self.remInstr)
        
        instrpoolLayout.addWidget(self.instrpool_label)
        instrpoolLayout.addWidget(self.instrpool_tree)
        instrpoolLayout.addItem(instrpool_buttonsLayout)

        horLayout.addItem(instrpoolLayout)
        
        
        meassetupLayout = QtWidgets.QVBoxLayout()
        
        self.meassetup_label=QtWidgets.QLabel()
        self.meassetup_label.setText('Measurement Setup')
        
        self.meassetup_tree = QtWidgets.QTreeView()
        ## change tree behavior later 
        self.meassetup_tree.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.meastree_model = QtGui.QStandardItemModel()
        self.meassetup_tree.setModel(self.meastree_model)
        ##
        
       

        meassetup_buttonsLayout = QtWidgets.QHBoxLayout()
        
        self.addPar = QtWidgets.QPushButton()
        self.addPar.setText('Add')
        self.editPar = QtWidgets.QPushButton()
        self.editPar.setText('Edit')
        self.remPar = QtWidgets.QPushButton()
        self.remPar.setText('Remove')
        
        meassetup_buttonsLayout.addWidget(self.addPar)
        meassetup_buttonsLayout.addWidget(self.editPar)
        meassetup_buttonsLayout.addWidget(self.remPar)
        
        
        meassetup_commentsLayout = QtWidgets.QVBoxLayout()
        
        self.meassetup_comments_label = QtWidgets.QLabel()
        self.meassetup_comments_label.setText('Comments')
        
        self.meassetup_comments_text = QtWidgets.QTextEdit()
        
        meassetup_commentsLayout.addWidget(self.meassetup_comments_label)
        meassetup_commentsLayout.addWidget(self.meassetup_comments_text)
        
        meassetup_timingLayout = QtWidgets.QVBoxLayout()
        
        self.meassetup_timing_label = QtWidgets.QLabel()
        self.meassetup_timing_label.setText('Timming')
        
        meassetup_timing_predictedLayout = QtWidgets.QHBoxLayout()
        self.meassetup_timing_predicted_label = QtWidgets.QLabel()
        self.meassetup_timing_predicted_label.setText('Time needed: ')
        self.meassetup_timing_predicted_value = QtWidgets.QLabel()
        self.meassetup_timing_predicted_value.setText('00:00:00')
        
        
        meassetup_timing_predictedLayout.addWidget(self.meassetup_timing_predicted_label)
        meassetup_timing_predictedLayout.addWidget(self.meassetup_timing_predicted_value)
        meassetup_timingLayout.addItem(meassetup_timing_predictedLayout)
        
        meassetup_extraLayout = QtWidgets.QHBoxLayout()
        meassetup_extraLayout.addItem(meassetup_commentsLayout)
        meassetup_extraLayout.addItem(meassetup_timingLayout)
        
        
        
        meassetupLayout.addWidget(self.meassetup_label)
        meassetupLayout.addWidget(self.meassetup_tree)
        meassetupLayout.addItem(meassetup_buttonsLayout)
        meassetupLayout.addItem(meassetup_extraLayout)
        
        horLayout.addItem(meassetupLayout)
 
        widget = QtWidgets.QWidget()
        widget.setLayout(horLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Measurement Creator')
        self.setGeometry(1000, 30, 1200, 400)

        # self.updatecallback()
        self.show()

        self.populate_instruments()
        
        instr_module=importlib.import_module('custom_loops.NEInstruments')
        self.populate_classes(instr_module)
        
        self.update_intrumentpool_tree()
        
        self.stored_instrument_settings={}
        
## -------------- GUI functions 


    def populate_classes(self,instrument_module):
        clsmembers = inspect.getmembers(instrument_module, inspect.isclass)
        # print(clsmembers)
        clsmembers_names = list(zip(*clsmembers))[0]
        # print(self.clsmembers)
        instr=[]
        self.module_instruments_dict={}
        for _class in clsmembers:
            # print(_class)
            # print('')
            class_functions=inspect.getmembers(_class[1],inspect.isclass)
            
            instr_functions=[]
            for function in class_functions:
                # print(function)
                # print(getattr(_class[1],function[0]))
                # print(inspect.signature(function[1]))
                # print(function[1].__code__.co_varnames)
                # if '_is_instrument_function' in function[1].__code__.co_varnames:
                try:
                    function[1]._is_physical_instrument
                    # print(function)
                    instr_functions.append(function)
                except:
                    pass
                    # print('Not an instrument class')
            self.module_instruments_dict[_class[0]]=instr_functions
            # self.module_instruments_drivers=[self.module_instruments_dict._driver_path for instrument in _class for _class in ]
            
            

        # print(clsmembers_names)
        # print(self.module_instruments_dict)
        # print(instr)
    
    def populate_instruments(self):
        self.station_instruments_dict = self.main.station.components
        self.station_instruments_keys = list(self.main.station.components.keys())
        self.station_instruments_drivers = [self.main.station.components[key].__class__.__module__ for key in self.station_instruments_keys]
        # print(self.station_instruments_drivers)
        
    def update_intrumentpool_tree(self):
        model = self.instrtree_model
        
        model.clear()
        # model.setHorizontalHeaderLabels(
                    # ['Class', 'Instrument', 'Value', 'Status' ])
        
        model.setHorizontalHeaderLabels(
            ['Instrument', 'Value', 'Class', 'Driver', 'Station name', 'Module name'])
        
        instrument_classes_dict=self.module_instruments_dict
  
        
        ## sorted by available instruments
        
        for instrument in self.station_instruments_dict:
            instrument_module=self.main.station.components[instrument]
            instrument_parent=QtGui.QStandardItem(str(instrument_module))
            for class_name in instrument_classes_dict:
                for instrument_function in instrument_classes_dict[class_name]:
                    # print(instrument_function[1]._driver_path)
                    # print(instrument_module.__class__.__module__)
                    if instrument_module.__class__.__module__ == instrument_function[1]._driver_path:
                        # print('found')
                        instrument_class=class_name
                        instrument_driver=instrument_module.__class__.__module__
                        selected_instrument_class=instrument_function[1]
                        # print(class_name)
                    # else:
                        # print('not found')
                        
            instrument_class_parameters=QtGui.QStandardItem('Class parameters')
            instrument_parent.appendRow(instrument_class_parameters)
            selected_instrument_class._parameter_dictionary
            # instrument_parent.parameters
            instrument_driver_paramaters=QtGui.QStandardItem('Driver parameters')
            for driver_par in instrument_module.parameters:
                try:
                    par_value = instrument_module.parameters[driver_par].get()
                except:
                    par_value = None
                    
                par_value=QtGui.QStandardItem(str(par_value))
                driver_par=QtGui.QStandardItem(driver_par)
                
                instrument_driver_paramaters.appendRow([driver_par, par_value])
               
            instrument_parent.appendRow(instrument_driver_paramaters)
            
            
            model.appendRow([instrument_parent, QtGui.QStandardItem(), QtGui.QStandardItem(class_name), QtGui.QStandardItem(instrument_driver), QtGui.QStandardItem(instrument_module.name), QtGui.QStandardItem(str(instrument_function[1]))])
            # self.instrument_class_parameters=
            
            self.instrpool_tree.setColumnHidden(5, True)
            
    def check_item_for_buttons(self,item_index):
        
        item_str=item_index.data()
        if item_str == 'Class parameters':
            self.addInstr.setEnabled(True)
        else:
            self.addInstr.setEnabled(False)
        
            
    def add_parameter(self,instrument_index):
            # print(dir(instrument_index))
            # print(instrument_index.row())
            # print(self.instrtree_model.item(instrument_index.row(),1).text())
        print(self.instrtree_model.item(instrument_index.row(),4).text())
        instrument_class=self._get_module_instrument_class(instrument_index)
        self.new_par = add_parameter_GUI(instrument_class._parameter_dictionary)
            



    def _get_module_instrument_class(self, instrument_index):
        
        instrument_classes_dict=self.module_instruments_dict
        
        instrument_name = self.instrtree_model.item(instrument_index.row(),4).text()
        print(instrument_name)
        
        instrument_module=self.main.station.components[instrument_name]
        instrument_parent=QtGui.QStandardItem(str(instrument_module))
        for class_name in instrument_classes_dict:
            for instrument_function in instrument_classes_dict[class_name]:
                # print(instrument_function[1]._driver_path)
                # print(instrument_module.__class__.__module__)
                if instrument_module.__class__.__module__ == instrument_function[1]._driver_path:
                    # print('found')
                    instrument_class=class_name
                    instrument_driver=instrument_module.__class__.__module__
                    selected_instrument_class=instrument_function[1]
                    
        return selected_instrument_class

        
        
        
        
class add_parameter_GUI(QtWidgets.QMainWindow):
    
    def __init__(self, instrument_dictionary, parent=None):
        super(add_parameter_GUI, self).__init__(parent)

        self.main=parent
        
        
        vertLayout = QtWidgets.QVBoxLayout()   
        
        widget_dict={}
        for key in instrument_dictionary:
            horLayout = QtWidgets.QHBoxLayout()   
            
            widget_dict[key]=[]
            
            par_name_widget = QtWidgets.QLabel()
            par_name_widget.setText(key)
            par_value_widget = QtWidgets.QLineEdit()
            horLayout.addWidget(par_name_widget)
            horLayout.addWidget(par_value_widget)
            
            vertLayout.addItem(horLayout)
        
        
        
        widget = QtWidgets.QWidget()
        widget.setLayout(vertLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Add parameter')
        self.setGeometry(1000, 30, 200, 400)
        
        self.show()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        ## sorted by instrument class
   
        # for class_name in instrument_classes_dict:
            # class_item=QtGui.QStandardItem(class_name)
            
            # for instrument_function in instrument_classes_dict[class_name]:
                # print(instrument_function)
                # print(instrument_function[1]._driver_path)
                # instrument_item=QtGui.QStandardItem(instrument_function[0])
                
                # if instrument_function[1]._driver_path in self.station_instruments_drivers:
                    # status='Active'
                # else:
                    # status='Inactive'
                    
                
                # class_item.appendRow([QtGui.QStandardItem(), instrument_item, QtGui.QStandardItem(), QtGui.QStandardItem(status) ])

            # model.appendRow(class_item)
        