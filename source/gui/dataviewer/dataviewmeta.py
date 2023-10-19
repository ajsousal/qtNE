import argparse
import logging
import os

import pyqtgraph as pg
import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
from qtpy.QtWidgets import QFileDialog, QWidget

import qcodes

from qcodes.plots.pyqtgraph import QtPlot
# from source.gui.helpers import data_array
from qcodes.data import data_array


class DataMeta(QtWidgets.QDialog):

	def __init__(self, parent=None):
		super(DataMeta, self).__init__(parent)

		self.main=parent

		self.meta_tabs = QtWidgets.QTabWidget()
		self.meta_tabs.addTab(QtWidgets.QWidget(), 'metadata')
		

		treesLayout = QtWidgets.QHBoxLayout()
		treesLayout.addWidget(self.meta_tabs)

		self.setWindowTitle('Metadata Viewer')
		

		self.setLayout(treesLayout)
		self.setGeometry(500, 660, 500, 300) # x y w h
		self.show()



	def _create_meta_tree(self, meta_dict):
		metatree = QtWidgets.QTreeView()
		_metamodel = QtGui.QStandardItemModel()
		metatree.setModel(_metamodel)
		metatree.setEditTriggers(
			QtWidgets.QAbstractItemView.NoEditTriggers)

		_metamodel.setHorizontalHeaderLabels(['parameter', 'value'])

		try:
			self.main.fill_item(_metamodel, meta_dict)
			return metatree

		except Exception as ex:
			print(ex)


	def update_meta_tabs_v2(self):
		meta = self.main.dict_fixed

		self.meta_tabs.clear()

		metatree = QtWidgets.QTreeView()
		_metamodel = QtGui.QStandardItemModel()
		metatree.setModel(_metamodel)
		metatree.setEditTriggers(
			QtWidgets.QAbstractItemView.NoEditTriggers)
		_metamodel.setHorizontalHeaderLabels(['Parameter','Value'])
	
		for param, value in zip(meta[list(meta.keys())[0]], meta[list(meta.keys())[1]]):
			parent = [QtGui.QStandardItem(str(param)), QtGui.QStandardItem(str(value))]
			_metamodel.appendRow(parent)
		self.meta_tabs.addTab(metatree,'Fixed parameters')

		return
	
	def update_meta_tabs(self):
		''' Update metadata tree '''
		meta = self.main.dataset.metadata

		self.meta_tabs.clear()
		if 'gates' in meta.keys():
			self.meta_tabs.addTab(self._create_meta_tree(meta['gates']),
			                      'gates')
		elif meta.get('station', dict()).get('instruments', dict()).get('gates', None) is not None:
			self.meta_tabs.addTab(
				self._create_meta_tree(
					meta['station']['instruments']['gates']),
				'gates')
		if meta.get('station', dict()).get('instruments', None) is not None:
			if 'instruments' in meta['station'].keys():
				self.meta_tabs.addTab(
					self._create_meta_tree(
						meta['station']['instruments']),
					'instruments')

		self.meta_tabs.addTab(self._create_meta_tree(meta), 'metadata')



	def update_implicit_gates(self):
		data=self.main.dataset
		data_implicit=[]
		
		for kk in range(len(data.arrays)):
			if data.arrays[list(data.arrays)[kk]].array_id.find('_cb')!=-1 or data.arrays[list(data.arrays)[kk]].array_id.find('_fix')!=-1:				
				data_implicit.append(data.arrays[list(data.arrays)[kk]])

		self.meta_tabs.addTab(self._create_meta_implicit(data_implicit),'Implicit gates') # replace with custom-mad function reading array
	

	def _create_meta_implicit(self,data_impl):
		metatree = QtWidgets.QTreeView()
		_metamodel = QtGui.QStandardItemModel()
		metatree.setModel(_metamodel)
		metatree.setEditTriggers(
			QtWidgets.QAbstractItemView.NoEditTriggers)

		_metamodel.setHorizontalHeaderLabels(['name', 'type', 'value'])

		try:
			self.fill_implicit(_metamodel,data_impl)
			return metatree

		except Exception as ex:
			print(ex)		


	def fill_implicit(self,mmodel,item):
		for it in item:
			if isinstance(it,qcodes.data.data_array.DataArray):
			# if isinstance(it,data_array.DataArray):
				if it.array_id.find('_cbsweep')!=-1:
					if len(it.ndarray.shape)>1:
						arraytowrite=str(it.ndarray[0]) 
					else: 
						arraytowrite=str(it.ndarray)
					
					child = [QtGui.QStandardItem(str(it.label)), # why not name???
	        				 QtGui.QStandardItem(str('combined sweep')),
	                         QtGui.QStandardItem(arraytowrite)]	   
					mmodel.appendRow(child)
				
				if it.array_id.find('_cbstep')!=-1:
					child = [QtGui.QStandardItem(str(it.label)), # why not name???
	        				 QtGui.QStandardItem(str('combined step')),
	                         QtGui.QStandardItem(str(it.ndarray))]	   
					mmodel.appendRow(child)					

				if it.array_id.find('_fix')!=-1:
					if len(it.ndarray.shape)>1:
						arraytowrite=str(it.ndarray[0][0]) 
					else: 
						arraytowrite=str(it.ndarray[0])
					
					child = [QtGui.QStandardItem(str(it.label)), # why not name???
	        				 QtGui.QStandardItem(str('fixed')),
	        				 QtGui.QStandardItem(arraytowrite)]
					mmodel.appendRow(child)
			else:
				return
