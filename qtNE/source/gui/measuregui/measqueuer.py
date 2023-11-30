import os
import time

import pyqtgraph as pg
import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
from qtpy.QtWidgets import QFileDialog, QWidget

import json
import pickle
from tempfile import gettempdir

import shutil
from stat import S_IREAD, S_IRWXU



class MeasQueuer(QtWidgets.QDialog):

	def __init__(self, parent=None, temp_dir=None):
		super(MeasQueuer, self).__init__(parent)

		self.main=parent

		self.temp_dir=temp_dir


		self.queue=QtWidgets.QListView()
		self.queue.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
		self.queue.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		# self.queue.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

		self._queue = QtGui.QStandardItemModel()
		self.queue.setModel(self._queue)


		self.addmeas = QtWidgets.QPushButton()
		self.addmeas.setText('Add file')

		self.addfolder = QtWidgets.QPushButton()
		self.addfolder.setText('Add folder')

		self.openmeas = QtWidgets.QPushButton()
		self.openmeas.setText('Open file')

		self.deletemeas = QtWidgets.QPushButton()
		self.deletemeas.setText('Delete file')

		self.clearqueue = QtWidgets.QPushButton()
		self.clearqueue.setText('Clear queue')

		self.RunMeasurement = QtWidgets.QPushButton()
		self.RunMeasurement.setText('Run')

		self.StopMeasurement = QtWidgets.QPushButton()
		self.StopMeasurement.setText('Stop')


		queueLayout = QtWidgets.QHBoxLayout()
		buttonLayout = QtWidgets.QHBoxLayout()
		buttonLayout2 = QtWidgets.QHBoxLayout()

		buttonLayout.addWidget(self.addfolder)
		buttonLayout.addWidget(self.addmeas)
		buttonLayout.addWidget(self.openmeas)
		buttonLayout.addWidget(self.deletemeas)

		buttonLayout2.addWidget(self.RunMeasurement)
		buttonLayout2.addWidget(self.StopMeasurement)

		queueLayout.addWidget(self.queue)

		vertLayout = QtWidgets.QVBoxLayout()

		vertLayout.addItem(queueLayout)
		vertLayout.addItem(buttonLayout)
		vertLayout.addItem(buttonLayout2)

		self.setWindowTitle('Measurement Queuer')

		self.setLayout(vertLayout)
		self.show()

		self.addfolder.clicked.connect(self.addfolder_callback)
		self.addmeas.clicked.connect(self.addmeas_callback)
		self.openmeas.clicked.connect(self.openmeas_callback)
		self.deletemeas.clicked.connect(self.deletemeas_callback)

		self.RunMeasurement.clicked.connect(self.main.runmeas_callback)
		self.StopMeasurement.clicked.connect(self.main.stopmeas_callback)

		self.update_logs()

		self.StopMeasurement.setEnabled(False)
		if self.queue.model().rowCount()==0:
			self.RunMeasurement.setEnabled(False)


	def addfolder_callback(self):

		try:
			foldername = QFileDialog.getExistingDirectory(self, 'Open experiment', self.main.current_directories['current_meas'])
			print(foldername)
		except:
			print('No folder selected.')

		for fname in os.listdir(foldername):
			print(fname)
			namemeas=time.strftime('%Y%m%d',time.localtime())+'_'+time.strftime('%H%M%S',time.localtime())+'_'+os.path.basename(fname)
			shutil.copyfile(os.path.join(foldername,fname),os.path.join(self.temp_dir,namemeas))
			os.chmod(os.path.join(self.temp_dir,namemeas), S_IREAD)

		
		print('Added '+str(len(os.listdir(foldername)))+' files to measurement queue.')
		self.update_logs()

		# if self.queue.model().rowCount()>0:
		if self.queue.model().rowCount()>0 and self.main.meas_running==False:
			self.RunMeasurement.setEnabled(True)

	def addmeas_callback(self):

		try:
			fname, filters = QFileDialog.getOpenFileName(self, 'Open experiment', self.main.current_directories['current_meas'] , 'Experiment (*.json *.py)')
			namemeas=time.strftime('%Y%m%d',time.localtime())+'_'+time.strftime('%H%M%S',time.localtime())+'_'+os.path.basename(fname)
			shutil.copyfile(fname,os.path.join(self.temp_dir,namemeas))
			os.chmod(os.path.join(self.temp_dir,namemeas), S_IREAD)
		except:
			print('No file selected.')

		self.update_logs()

		# if self.queue.model().rowCount()>0:
		if self.queue.model().rowCount()>0 and self.main.meas_running==False:
			self.RunMeasurement.setEnabled(True)


	def openmeas_callback(self):

		indices = self.queue.selectionModel().selectedRows() 
		for index in sorted(indices):
			os.startfile(index.data())


	def deletemeas_callback(self):

		indices = self.queue.selectionModel().selectedRows() 
		# print(indices)
		for index in sorted(indices):
			# print(index.data())
			os.chmod(index.data(), S_IRWXU)
			os.remove(index.data())

		self.update_logs()


	def clearqueue_callback(self):
		print('')
	def update_logs(self):
		''' Update the list of measurements '''

		dd= [os.path.join(self.temp_dir,f) for f in os.listdir(self.temp_dir) if (f.endswith('.json') or f.endswith('.py'))] #os.path.join(self.temp_dir, file)

		self._queue.clear()
		# model.setHorizontalHeaderLabels(
			# ['Log', 'Sample', 'location', 'filename', 'Setpoints', 'Outputs', 'Comments'])

		for _, filename in enumerate(dd):
			child = QtGui.QStandardItem(filename)
			self._queue.appendRow(child)

