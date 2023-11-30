import os

import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
# from qtpy.QtWidgets import QFileDialog, QWidget
import qtpy.QtCore as QtCore
# import sys
# sys.path.append('..//..')
from ..helpers import procstyles as procstyles

import six

import json

class Function(QtWidgets.QWidget):
	def __init__(self, name, main, signal, func, widgets=[]):
		super(Function, self).__init__(None)

		layout = QtWidgets.QGridLayout(self)
		self.name = name
		self.main = main
		self.func = func
		self.items = {}
		self.types = {}
		self.signal=signal
		height = 1

		# For every parameter in the Operation widget, create the appropriate
		# parameter widget depending on the data type
		for widget in widgets:
			w_name, data = widget

			if type(data) == bool:
				checkbox = QtWidgets.QCheckBox(w_name)
				checkbox.setChecked(data)
				# checkbox.stateChanged.connect(self.main.on_data_change)
				layout.addWidget(checkbox, height, 2)
				checkbox.stateChanged.connect(self.toggle_apply)

				self.items[w_name] = checkbox
			elif type(data) == int or type(data) == float:
				lineedit = QtWidgets.QLineEdit(str(data))
				lineedit.setValidator(QtGui.QDoubleValidator())
				layout.addWidget(QtWidgets.QLabel(w_name), height, 1)
				layout.addWidget(lineedit, height, 2)
				lineedit.textEdited.connect(self.toggle_apply)

				self.items[w_name] = lineedit
			elif type(data) == list:
				layout.addWidget(QtWidgets.QLabel(w_name), height, 1)
				combobox = QtWidgets.QComboBox()
				# combobox.activated.connect(self.main.on_data_change)
				combobox.addItems(data)
				layout.addWidget(combobox, height, 2)
				combobox.currentIndexChanged.connect(self.toggle_apply)

				self.items[w_name] = combobox

			self.types[w_name] = type(data)

			height += 1

	def get_parameter(self, name):
		if name in self.items:
			widget = self.items[name]
			cast = self.types[name]

			if type(widget) is QtWidgets.QCheckBox:
				return cast(widget.isChecked())
			elif type(widget) is QtWidgets.QLineEdit:
				return cast(str(widget.text()))
			elif type(widget) is QtWidgets.QComboBox:
				return str(widget.currentText())

	def set_parameter(self, name, value):
		if name in self.items:
			widget = self.items[name]

			if type(widget) is QtWidgets.QCheckBox:
				widget.setChecked(bool(value))
			elif type(widget) is QtWidgets.QLineEdit:
				widget.setText(str(value))
			elif type(widget) is QtWidgets.QComboBox:
				index = widget.findText(value)
				widget.setCurrentIndex(index)

	def get_parameters(self):
			
		params = {name: self.get_parameter(name) for name in self.items}

		return self.name, params

	def set_parameters(self, params):
		for name, value in params.items():
			self.set_parameter(name, value)

	def toggle_apply(self):
		self.signal.emit()



class DataFuncs(QtWidgets.QDialog):


	sigapply = QtCore.Signal()
		

	def __init__(self, parent=None):
		super(DataFuncs, self).__init__(parent)

		self.main=parent

		pathname = os.path.dirname(os.path.abspath(__file__))
		self.filename=os.path.join(pathname,'recipes')
		open(self.filename,'a').close()


		self.sigapply.connect(self.on_widget_change)
		# Buttons

		self.addFunc = QtWidgets.QPushButton()
		self.addFunc.setText('Add')
		# self.addFunc.setCheckable(True)

		self.upFunc = QtWidgets.QPushButton()
		self.upFunc.setText('Up')
		# self.addFunc.setCheckable(True)

		self.downFunc = QtWidgets.QPushButton()
		self.downFunc.setText('Down')
		# self.addFunc.setCheckable(True)

		self.removeFunc = QtWidgets.QPushButton()
		self.removeFunc.setText('Remove')
		# self.addFunc.setCheckable(True)

		self.clearFunc = QtWidgets.QPushButton()
		self.clearFunc.setText('Clear')
		# self.addFunc.setCheckable(True)

		self.applyFunc = QtWidgets.QPushButton()
		self.applyFunc.setText('Apply')
		# self.addFunc.setCheckable(True)

		self.saveFunc = QtWidgets.QPushButton()
		self.saveFunc.setText('Save...')
		# self.addFunc.setCheckable(True)

		self.loadFunc = QtWidgets.QPushButton()
		self.loadFunc.setText('Load...')
		# self.addFunc.setCheckable(True)


		# Trees and lists

		self.funcsTree = QtWidgets.QListWidget()

		self.applyTree = QtWidgets.QListWidget(self)


		## parameters of functions 

		self.stack = QtWidgets.QStackedWidget()

		self.recipename = QtWidgets.QComboBox()

		self.addrecipe = QtWidgets.QPushButton()
		self.addrecipe.setText('+')
		self.addrecipe.setMaximumWidth(30)

		self.removerecipe = QtWidgets.QPushButton()
		self.removerecipe.setText('-')
		self.removerecipe.setMaximumWidth(30)

		# labels

		self.availablelabel = QtWidgets.QLabel()
		self.availablelabel.setText('Available operations')
		self.toapplylabel = QtWidgets.QLabel()
		self.toapplylabel.setText('Operations to apply')
		self.descriptionlabel = QtWidgets.QLabel()
		self.descriptionlabel.setText('Function description here...')
		self.recipelabel = QtWidgets.QLabel()
		self.recipelabel.setText('Saved Recipes')


		leftLayout = QtWidgets.QVBoxLayout()
		centerLayout = QtWidgets.QVBoxLayout()
		rightLayout = QtWidgets.QVBoxLayout()

		ccLayout=QtWidgets.QVBoxLayout()
		cLayout = QtWidgets.QHBoxLayout()
		bottomLayout = QtWidgets.QHBoxLayout()
		recLayout = QtWidgets.QHBoxLayout()

		leftLayout.addWidget(self.availablelabel)
		leftLayout.addWidget(self.funcsTree)

		# self.recipeTree.setMaximumHeight(40)

		centerLayout.addWidget(self.addFunc)
		centerLayout.addWidget(self.upFunc)
		centerLayout.addWidget(self.downFunc)
		centerLayout.addWidget(self.removeFunc)
		centerLayout.addWidget(self.clearFunc)
		centerLayout.addWidget(self.applyFunc)


		recLayout.addWidget(self.recipename)
		recLayout.addWidget(self.addrecipe)
		recLayout.addWidget(self.removerecipe)

		rightLayout.addWidget(self.recipelabel)
		rightLayout.addItem(recLayout)
		rightLayout.addWidget(self.toapplylabel)
		rightLayout.addWidget(self.applyTree)
		rightLayout.addWidget(self.stack)
		self.stack.hide()

		bottomLayout.addWidget(self.descriptionlabel)

		cLayout.addItem(leftLayout)
		cLayout.addItem(centerLayout)
		cLayout.addItem(rightLayout)

		ccLayout.addItem(cLayout)
		ccLayout.addItem(bottomLayout)


		self.addFunc.clicked.connect(self.add_function)
		self.removeFunc.clicked.connect(self.remove_function)
		self.upFunc.clicked.connect(self.up_function)
		self.downFunc.clicked.connect(self.down_function)
		self.clearFunc.clicked.connect(self.clear_functions)
		self.funcsTree.currentItemChanged.connect(self.on_select_option)
		self.applyTree.currentItemChanged.connect(self.on_selected_changed)
		self.applyFunc.clicked.connect(self.on_apply_function)
		self.recipename.activated.connect(self.on_recipe_changed)
		self.addrecipe.clicked.connect(self.add_recipe)
		self.removerecipe.clicked.connect(self.remove_recipe)



		self.setWindowTitle('Post-processing')
		
		self.setLayout(ccLayout)
		self.setGeometry(500, 300, 500, 300)
		self.show()


		self.last_selection=None

		# self.functions = {func_name :{[function_method, directional, parameters]}
		self.functions = {
			'abs': [procstyles.f_abs],
			'filt_highpass': [procstyles.f_highpass, [('x_width', 3.0),
										   ('y_height', 3.0), ('method', [
												'gaussian',
												'lorentzian',
												'exponential',
												'thermal'])]],
			# 'interp_x': [procstyles.f_xinterp, [('points', 100)]],
			# 'interp_y': [procstyles.f_yinterp, [('points', 100)]],
			'log': [procstyles.f_log, [('axis',['x','y'])]],
			'filt_lowpass': [procstyles.f_lowpass, [('x_width', 3.0),
										 ('y_height', 3.0),
										 ('method', ['gaussian',
													 'lorentzian',
													 'exponential',
													 'thermal'])]],
			'int_x': [procstyles.f_xintegrate],
			'int_y': [procstyles.f_yintegrate],
			'filt_movavg': [procstyles.f_movavg, [('m', 2), ('n', 3)]],					   

			'deinterlace': [procstyles.f_deinterlace, [('indices', ['odd', 'even'])]],			#								  '2nd order central diff'])]],
			'deriv_x': [procstyles.f_xderiv,  [('method', ['numerical','smooth']), ('sigma', 2)]],
			'deriv_y': [procstyles.f_yderiv, [('method', ['numerical','smooth']),('sigma', 2)]],
			'filt_savgol': [procstyles.f_savgol, [('samples', 5), ('order', 2)]],
			'offset': [procstyles.offset, [('value',-0.03)]],
			'remove_bg': [procstyles.remove_bg_line,[('axis', ['x', 'y'])]]
								}


		self.funcqueue={}

		self.funcsTree.addItems(sorted(self.functions.keys()))
		self.load_recipes()



	def add_function(self):

		if self.funcsTree.currentItem():
			name = str(self.funcsTree.currentItem().text())

			item = QtWidgets.QListWidgetItem(name)
			item.setCheckState(QtCore.Qt.Checked)
			operation = Function(name, self.main, self.sigapply, *self.functions[name])
			# print(operation)

			if six.PY2:
				item.setData(QtCore.Qt.UserRole, QtCore.QVariant(operation))
			elif six.PY3:
				item.setData(QtCore.Qt.UserRole, operation)

			# self.stack.hide()
			self.stack.addWidget(operation)
			# self.stack.show()
			# self.stack.updateGeometry()

			self.applyTree.addItem(item)
			self.applyTree.setCurrentItem(item)

			self.applyFunc.setEnabled(True)



	def remove_function(self):
		self.applyTree.takeItem(self.applyTree.currentRow())
		# self.funcqueue.pop(self.applyTree.currentItem().text())
		if self.applyTree.count()==0:
			self.stack.hide()
			self.clear_functions()
			# self.applyFunc.setEnabled(False)
		
		self.applyFunc.setEnabled(True)



	def up_function(self):
		selected_row = self.applyTree.currentRow()
		current = self.applyTree.takeItem(selected_row)
		self.applyTree.insertItem(selected_row - 1, current)
		self.applyTree.setCurrentRow(selected_row - 1)
		self.applyFunc.setEnabled(True)



	def down_function(self):
		selected_row = self.applyTree.currentRow()
		current = self.applyTree.takeItem(selected_row)
		self.applyTree.insertItem(selected_row + 1, current)
		self.applyTree.setCurrentRow(selected_row + 1)
		self.applyFunc.setEnabled(True)



	def clear_functions(self):
		self.applyTree.clear()
		self.stack.hide()

		self.funcqueue={}
		self.funcqueue['identity']=[procstyles.f_identity, {}]
		try:
			self.main.functionsqueue_callback(self.funcqueue,self.main.dataset)
		except:
			print('No plot active.')
		self.applyFunc.setEnabled(False)



	def on_selected_changed(self, current, previous):
		if current:
			if six.PY2:
				widget = current.data(QtCore.Qt.UserRole).toPyObject()
			elif six.PY3:
				widget = current.data(QtCore.Qt.UserRole)

			if len(widget.get_parameters()[1])>0:
				self.stack.hide()
				self.stack.addWidget(widget)
				self.stack.setCurrentWidget(widget)
				self.stack.show()
			else:
				self.stack.hide()



	def on_select_option(self, current, previous):
		if current:
			description = self.functions[str(current.text())][0].__doc__
			self.descriptionlabel.setText(description)



	def on_apply_function(self):
		self.funcqueue={}
		uniquecount=0
		for i in range(self.applyTree.count()):
			item = self.applyTree.item(i)

			if item.checkState() == QtCore.Qt.Unchecked:
				continue

			# if six.PY2:
			#	op = item.data(QtCore.Qt.UserRole).toPyObject()
			# elif six.PY3:
			op = item.data(QtCore.Qt.UserRole)

			testname, testpars=op.get_parameters()
			# print(op.get_parameters())
			# print(testname)
			# print(testpars)
			name_in_queue=testname
			if testname in self.funcqueue:
				uniquecount+=1
				# print('already exists')
				name_in_queue=testname+str(uniquecount)
			self.funcqueue[name_in_queue]=[self.functions[testname][0], testpars]
			#self.funcqueue[testname]=[self.functions[testname][0], testpars]
		#print(self.funcqueue)
		self.main.functionsqueue_callback(self.funcqueue,self.main.dataset)
		self.applyFunc.setEnabled(False)



	def on_widget_change(self):
		self.applyFunc.setEnabled(True)




	def on_recipe_changed(self):

		self.clear_functions()
		operations=self.recipes[self.recipename.currentText()]

		for i in sorted(operations):
			operation = operations[i]

			enabled = operation['enabled']

			# The key that doesn't have the value 'enabled' is the name
			for key in operation:
				if key != 'enabled':
					name = key

			# Create the item for the operations list
			item = QtWidgets.QListWidgetItem(name)

			if enabled:
				item.setCheckState(QtCore.Qt.Checked)
			else:
				item.setCheckState(QtCore.Qt.Unchecked)

			op = Function(name, self.main, self.sigapply, *self.functions[name])
			op.set_parameters(operation[name])

			# Store the Operation in the widget
			if six.PY2:
				item.setData(QtCore.Qt.UserRole, QtCore.QVariant(op))
			elif six.PY3:
				item.setData(QtCore.Qt.UserRole, op)

			self.stack.addWidget(op)

			self.applyTree.addItem(item)
			self.applyTree.setCurrentItem(item)
		
		self.applyFunc.setEnabled(True)


	def load_recipes(self):

		self.recipename.clear()
		with open(self.filename, 'r') as f:
			try:
				self.recipes=json.load(f)
			except:
				self.recipes={}

		self.recipename.addItems(self.recipes.keys())

		

	def add_recipe(self):

		new_recipename, ok=QtWidgets.QInputDialog.getText(self, 'Recipe name prompt','Enter new recipe name: ')
		if ok: 

			operations = {}
			for i in range(self.applyTree.count()):
				item = self.applyTree.item(i)

				if six.PY2:
					op = item.data(QtCore.Qt.UserRole).toPyObject()
				elif six.PY3:
					op = item.data(QtCore.Qt.UserRole)

				name, params = op.get_parameters()
				enabled = self.applyTree.item(i).checkState() == QtCore.Qt.Checked

				operations[i] = {'enabled': enabled}
				operations[i][name] = params

			self.recipes[new_recipename]=operations

			# print(self.recipes)
			with open(self.filename, 'w') as f:
				f.write(json.dumps(self.recipes, indent=4))

		self.load_recipes()

		index = self.recipename.findText(new_recipename, QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.recipename.setCurrentIndex(index)


	def remove_recipe(self):
		if self.recipename.currentText()=='None':
			print('Error: cannot remove default recipe.')
		else:
			self.recipes.pop(self.recipename.currentText())

			with open(self.filename, 'w') as f:
				f.write(json.dumps(self.recipes, indent=4))

			self.load_recipes()
			self.on_recipe_changed()