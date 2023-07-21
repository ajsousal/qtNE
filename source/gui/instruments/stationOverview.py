import PyQt6.QtGui as QtGui
from PyQt6.QtWidgets import QFileDialog, QWidget, QApplication


import qtpy.QtWidgets as QtWidgets


class stationOverview(QtWidgets.QMainWindow):

    def __init__(self,station=None):

        super(stationOverview, self).__init__()

        self.station = station

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
        self.setGeometry(1000, 30, 300, 500)


        # disable edit
        self.stationtree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # self.logtree.clicked.connect(lambda: self.log_callback(
            # self.logtree.currentIndex()))  # self.log_callback)

        self.show()

        self._stationtreemodel.setHorizontalHeaderLabels(['Component','Driver'])
        self._parametertreemodel.setHorizontalHeaderLabels(['Parameter','Component']) ## ,'Settable'])

        self.fill_station_components()
        self.native_parameters_dict = self.return_parameter_list() # dictionary containing native parameters for every station component VIP: to be used also for autoGUI
        self.fill_parameter_list()

    def fill_station_components(self):

        parentItem = self._stationtreemodel.invisibleRootItem()
        
        for component in self.station.components:
            driver = self.station.components[component].__module__
            name = self.station.components[component].name

            name_item = QtGui.QStandardItem(name)
            driver_item = QtGui.QStandardItem(driver)
            parentItem.appendRow([name_item,driver_item])


    def return_parameter_list(self):
        parameters_dictionary = {}
        for component in self.station.components:
            parameters_dictionary[component] = list(self.station.components[component].parameters)

        return parameters_dictionary
            

    def fill_parameter_list(self):
        for component in self.station.components:
            parent = QtGui.QStandardItem(component)
            self._parametertreemodel.appendRow(parent)
            
            for parameter in self.station.components[component]:
                if parameter not in self.native_parameters_dict[component]:
                    child = QtGui.QStandardItem(parameter)
                    parent.appendRow(child)


## need to return station at some point