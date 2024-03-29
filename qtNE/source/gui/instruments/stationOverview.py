import PyQt6.QtGui as QtGui
from PyQt6.QtWidgets import QFileDialog, QWidget, QApplication
import qcodes


import qtpy.QtWidgets as QtWidgets

from .autoSF import autoSF


class stationOverview(QtWidgets.QMainWindow):

    def __init__(self,parent = None):

        super(stationOverview, self).__init__(parent)

        self.main = parent

        # self.database_dir = database_dir

        self.stationtree = QtWidgets.QTreeView()
        self.stationtree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._stationtreemodel = QtGui.QStandardItemModel()
        self.stationtree.setModel(self._stationtreemodel)

        self.parametertree = QtWidgets.QTreeView()
        self.parametertree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._parametertreemodel = QtGui.QStandardItemModel()
        self.parametertree.setModel(self._parametertreemodel)

        
        self.SoftPanel = QtWidgets.QPushButton()
        self.SoftPanel.setText('Soft Panel')

        self.AddParameter = QtWidgets.QPushButton()
        self.AddParameter.setText('Add')

        self.AddBatchParameter = QtWidgets.QPushButton()
        self.AddBatchParameter.setText('Add Batch')

        self.DeleteParameter = QtWidgets.QPushButton()
        self.DeleteParameter.setText('Delete')

        self.RefreshParameter = QtWidgets.QPushButton()
        self.RefreshParameter.setText('Refresh')


        horLayout = QtWidgets.QHBoxLayout()
        horLayout.addWidget(self.AddParameter)
        horLayout.addWidget(self.AddBatchParameter)
        horLayout.addWidget(self.DeleteParameter)
        horLayout.addWidget(self.RefreshParameter)

        treesLayout = QtWidgets.QVBoxLayout()
        treesLayout.addWidget(self.stationtree)
        treesLayout.addWidget(self.SoftPanel)
        treesLayout.addWidget(self.parametertree)
        treesLayout.addItem(horLayout)
        
        
        stackLayout = QtWidgets.QHBoxLayout()

        
        stackLayout.addItem(treesLayout)


        widget = QtWidgets.QWidget()
        widget.setLayout(stackLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Station Summary')
        self.stationtree.header().resizeSection(0, 280)
        self.parametertree.header().resizeSection(0, 280)
        self.setGeometry(1000, 30, 300, 500)


        ## disable tree edit
        self.stationtree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.parametertree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        

        ## Connect buttons

        self.SoftPanel.clicked.connect(self.generate_softpanel)

        self.AddParameter.clicked.connect(self.add_parameter)
        self.AddBatchParameter.clicked.connect(self.add_batch_parameters)
        self.DeleteParameter.clicked.connect(self.delete_parameter)
        self.RefreshParameter.clicked.connect(self.fill_parameter_list)

        self.softpanel = {}

        self.show()

        self._stationtreemodel.setHorizontalHeaderLabels(['Component','Driver'])
        self._parametertreemodel.setHorizontalHeaderLabels(['Parameter','Component']) ## ,'Settable'])

        self.fill_station_components()
        # self.native_parameters_dict = self.main.native_parameters_dict
        self.fill_parameter_list()

        ## Connect trees

        # self.parametertree.doubleClicked.connect(lambda dict_par = self.dict_par: self.open_parameter(dict_par))



    def fill_station_components(self):

        parentItem = self._stationtreemodel.invisibleRootItem()
        
        # print('station')
        for component in self.main.station.components:
            _instrument=self.main.station.components[component]
            
            # print( self.main.station.components[component].__class__ == 'qcodes.parameters.parameter.Parameter')
            if not (_instrument.__class__ == qcodes.parameters.parameter.Parameter):
                driver = _instrument.__module__
                name = _instrument.name

                instr_name_item = QtGui.QStandardItem(name)
                instr_driver_item = QtGui.QStandardItem(driver)
                Instr_item = [instr_name_item,instr_driver_item]
                parentItem.appendRow(Instr_item)
                
                for module in _instrument.submodules:
                    _submodule = _instrument.submodules[module]
                    
                    name  = _submodule.short_name
                    driver = _submodule.__module__
                    
                    submodule_name_item = QtGui.QStandardItem(name)
                    submodule_driver_item = QtGui.QStandardItem(driver)
                    
                    Modul_item = [submodule_name_item,submodule_driver_item]
                    instr_name_item.appendRow(Modul_item)
                
                
                


    def fill_parameter_list(self):
        ''' 
        Retrieves parameters that are not native of the instrument, eg. created for measurements
        '''
        
        # print('pars')
        # self._parametertreemodel.clear()

        parentItem2 = self._parametertreemodel.invisibleRootItem()

        for component in self.main.station.components:
            if self.main.station.components[component].__class__ == qcodes.parameters.parameter.Parameter: # not in self.native_parameters_dict[component]:
                parameter = component # self.main.station.components[component]
                try:
                    instrument = self.main.station.components[component].instrument.name
                except:
                    instrument = ''
                
                param_item = QtGui.QStandardItem(parameter)
                instr_item = QtGui.QStandardItem(instrument)
                parentItem2.appendRow([param_item,instr_item])

            # parent = QtGui.QStandardItem(component)
            # self._parametertreemodel.appendRow(parent)
            
            # for component in self.main.station.components:
            #     if self.main.station.components[component].__class__ is 'qcodes.parameters.parameter.Parameter': # not in self.native_parameters_dict[component]:
            #         child = QtGui.QStandardItem(parameter)
            #         parent.appendRow(child)


    def return_parameter_list(self):
        parameters_dictionary = {}
        for component in self.main.station.components:
            parameters_dictionary[component] = list(self.main.station.components[component].parameters)

        return parameters_dictionary
    


    def add_parameter(self):
        print()

    def add_batch_parameters(self):
        print()

    def delete_parameter(self):
        print()

    def generate_softpanel(self):

        instrument_index = self.stationtree.currentIndex()
        print(instrument_index.parent().data())
        ## TODO improve this solution
        try:
            instrument = self.main.station.components[instrument_index.data()]#Qt.DisplayRole)
        except:
            parent_instrument =instrument_index.parent().data()
            instrument = self.main.station.components[parent_instrument].submodules[instrument_index.data()]
        dictionary = instrument.parameters #self.native_parameters_dict[instrument.name]
        self.softpanel[instrument.name] = autoSF(instrument,dictionary) # TODO: create one instance per instruments
        
        # self.softpanel[instrument.name].create_gui()


    def open_parameter(parameter_dict):
        print()