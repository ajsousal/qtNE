import argparse
import logging
import os

import pyqtgraph as pg
import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
from qtpy.QtWidgets import QFileDialog, QWidget

import qcodes
from qcodes.plots.pyqtgraph import QtPlot


class DataProc(QtWidgets.QDialog):

	def __init__(self, parent=None):
		super(DataProc, self).__init__(parent)

		self.main=parent

		self.outCombo = QtWidgets.QComboBox()
		self.processCombo = QtWidgets.QComboBox()

		self.refreshPlot = QtWidgets.QPushButton()
		self.refreshPlot.setText('Refresh Plot')

		self.getCoord = QtWidgets.QPushButton()
		self.getCoord.setText('Get Coordinates')
		self.getCoord.setCheckable(True)

		self.getLinecut = QtWidgets.QPushButton()
		self.getLinecut.setText('Get line cut')
		self.getLinecut.setCheckable(True)

		self.processWindow = QtWidgets.QPushButton()
		self.processWindow.setText('Post-processing functions')
		self.processWindow.setCheckable(True)

		self.pptbutton = QtWidgets.QPushButton()
		self.pptbutton.setText('Send data to powerpoint')

		self.jpgbutton = QtWidgets.QPushButton()
		self.jpgbutton.setText('Export JPEG image')

		self.jupyterbutton = QtWidgets.QPushButton()
		self.jupyterbutton.setText('Generate Jupyter Notebook')


		self.freezeCmap = QtWidgets.QPushButton()
		self.freezeCmap.setText('Freeze Colormap')
		self.freezeCmap.setCheckable(True)

		self.autoWindow = QtWidgets.QPushButton()
		self.autoWindow.setText('Automated Analysis')
		self.autoWindow.setCheckable(True)


		## labels

		self.plotLabel=QtWidgets.QLabel()
		self.plotLabel.setText('Plotting tools')
		self.processLabel=QtWidgets.QLabel()
		self.processLabel.setText('Processing tools')
		self.exportLabel=QtWidgets.QLabel()
		self.exportLabel.setText('Export tools')

		bLayout = QtWidgets.QVBoxLayout()

		bLayout.addWidget(self.plotLabel)
		bLayout.addWidget(self.outCombo) # this is the output combobox
		bLayout.addWidget(self.refreshPlot)
		bLayout.addWidget(self.freezeCmap)

		bLayout.addWidget(self.processLabel)
		bLayout.addWidget(self.getCoord)
		bLayout.addWidget(self.getLinecut)
		bLayout.addWidget(self.processWindow)
		# bLayout.addWidget(self.processCombo)
		
		bLayout.addWidget(self.exportLabel)
		bLayout.addWidget(self.pptbutton)
		bLayout.addWidget(self.jpgbutton)
		bLayout.addWidget(self.jupyterbutton)
		# bLayout.addWidget(self.autoWindow)

		

		self.outCombo.currentIndexChanged.connect(self.main.combobox_callback)
		self.pptbutton.clicked.connect(self.main.ppt_callback)
		self.jpgbutton.clicked.connect(self.main.tojpg_callback)

		self.jupyterbutton.clicked.connect(self.main.jupyter_callback)


		self.refreshPlot.clicked.connect(self.main.refreshdata)

		self.getCoord.clicked.connect(self.main.toggle_getcoord)
		self.getLinecut.clicked.connect(self.main.toggle_linecut)
		self.processWindow.clicked.connect(self.main.toggle_procWindow)

		# self.autoWindow.clicked.connect(self.main.toggle_autoWindow)


		self.freezeCmap.clicked.connect(self.main.toggle_cmap)


		self.setWindowTitle('Data Controls')
		
		self.setLayout(bLayout)
		self.setGeometry(1200, 620, 150, 100)
		self.show()
