# %% Load packages

import numpy as np
import argparse
import logging
import os
import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.exporters import ImageExporter


import PyQt6.QtGui as QtGui
from PyQt6.QtWidgets import QFileDialog, QApplication
import qtpy.QtWidgets as QtWidgets

import qcodes

from source.gui.helpers.pyqtgraph_helper.pyqtgraph import QtPlot


try:
    from source.gui.helpers import procstyles as procstyles
except:
    pathit=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
    print(pathit)
    sys.path.append(pathit) # TO DO: make universal to source
    from source.gui.helpers import procstyles as procstyles


from source.gui.helpers import plot_tools
from source.tools import db_comms


try:
    from .dataviewmeta import DataMeta
    from .dataviewprocess import DataProc
    from .dataviewfunctions import DataFuncs
except:
    from dataviewmeta import DataMeta
    from dataviewprocess import DataProc
    from dataviewfunctions import DataFuncs


import pickle


import weakref
# from pyqtgraph.exporters import ImageExporter

from tempfile import gettempdir

#import h5py


# import debugpy
from PyQt6.QtCore import pyqtSignal

# %% Main class


class DataViewer(QtWidgets.QMainWindow): # QObject):#

    sig_msg = pyqtSignal(str)  # message to be shown to user

    def __init__(self, data_directory=None, window_title='Data browser',
                 default_parameter='amplitude', extensions=None, verbose=1, parent=None):
        """ Contstructs a simple viewer for Qcodes data.

        Args:
            data_directory (string or None): The directory to scan for experiments.
            default_parameter (string): A name of default parameter to plot.
            extensions (list): A list with the data file extensions to filter.
            verbose (int): The logging verbosity level.
        """
        super(DataViewer, self).__init__(parent)
        if extensions is None:
            extensions = ['dat', 'hdf5']

        
        # self.start_threads()

        self.main = parent

        self._update_plot_ = True

        # self.glayout=[[]]
        self.pplot = [[]]
        self.label = [[]]
        self.hLine = [[]]
        self.vLine = [[]]

        self.vLine_cut = [[]]
        self.hLine_cut = [[]]

        self.verbose = verbose
        self.default_parameter = default_parameter
        self.data_directories = [None] * 2
        self.directory_index = 0
        
        # data_directory='C:\qtNE_dbs_2021\Antonio'

        if data_directory is None:
            with open(os.path.join(gettempdir(), 'tmp'), "rb") as f:
                directories = pickle.load(f)
                print(directories)
            data_directory = directories['current_db']
            print(data_directory)

        try:
            # retrieved from StationGUI (parent)
            self.tmp_directory = self.main.tempdir
        except:
            print('Warning: Using current folder to store temporary files.')
            self.tmp_directory = os.getcwd()

        self.extensions = extensions

        # setup GUI
        self.dataset = None
        self.text = QtWidgets.QLabel()

        # logtree
        self.logtree = QtWidgets.QTreeView()
        self.logtree.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self._treemodel = QtGui.QStandardItemModel()
        self.logtree.setModel(self._treemodel)

# Initialize subwindows

        self.datameta = DataMeta(self)
        self.datameta.show()

        self.dataproc = DataProc(self)
        self.dataproc.show()

# -------

# ------------- horizontal layout
        topLayout = QtWidgets.QHBoxLayout()

        self.filterbutton = QtWidgets.QPushButton()
        self.filterbutton.setText('Filter data')
        self.filtertext = QtWidgets.QLineEdit()

        topLayout.addWidget(self.text)
        topLayout.addWidget(self.filterbutton)
        topLayout.addWidget(self.filtertext)

        treesLayout = QtWidgets.QHBoxLayout()
        treesLayout.addWidget(self.logtree)

# ------------- vertical layout
        vertLayout = QtWidgets.QVBoxLayout()

        vertLayout.addItem(topLayout)
        vertLayout.addItem(treesLayout)

        widget = QtWidgets.QWidget()
        widget.setLayout(vertLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle(window_title)
        self.logtree.header().resizeSection(0, 280)
        self.setGeometry(1000, 30, 500, 900)

# -------------

        # disable edit
        self.logtree.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)

        self.set_data_directory(data_directory)
        self.logtree.clicked.connect(lambda: self.log_callback(
            self.logtree.currentIndex()))  # self.log_callback)
        self.logtree.selectionModel().selectionChanged.connect(
            lambda: self.log_callback(self.logtree.currentIndex()))
        self.filterbutton.clicked.connect(
            lambda: self.update_logs(filter_str=self.filtertext.text()))

        menuBar = self.menuBar()

        menuDict = {
            '&Data': {'&Reload Data': self.update_logs,
                      #'&Preload all Info': self.load_info,
                      '&Quit': self.close},
            '&Folder': {'&Select Dir1': lambda: self.select_directory(index=0),
                        'Select &Dir2': lambda: self.select_directory(index=1),
                        '&Toggle Dirs': self.toggle_data_directory
                        },
            '&View': {'&Metadata Viewer': self.show_metadata,
                      'Data &Control': self.show_datacontrols
                      }
        }
        for (k, menu) in menuDict.items():
            mb = menuBar.addMenu(k)
            for (kk, action) in menu.items():
                act = QtWidgets.QAction(kk, self)
                mb.addAction(act)
                act.triggered.connect(action)

        if self.verbose >= 2:
            print('created gui...')

        # get logs from disk
        self.update_logs()
        self.datatag = None

        self.logtree.setColumnHidden(6, True) # DatabaseDir
        self.logtree.setColumnHidden(7, True) # Experiment
        self.show()


        self._current_db_conn = None # active db connection

        self._output_par = 'keith1_Idc1' # TODO: to be called/set from GUI
        

        # ----------- process data

        self.fqueue = {'identity': [procstyles.f_identity, {}]}

        self.numouts = 0

        self.qplotss = {'windows': [],
                        'positions': []}

        ## ['x_size (pixels)', 'y_size (pixels', 'x_position (relative)', 'y_positions (relative)']
        self.qplotss['positions'] = [[480, 640, 0, 0],
                                     [480, 640, 0.3, 0],
                                     [480, 640, 0.4, 0]
                                     ]

        self.current_ouputindex = 0
        self.current_outputpar = ['']


    def show_metadata(self):
        if not self.datameta.isVisible():
            self.datameta.show()

    def show_datacontrols(self):
        if not self.dataproc.isVisible():
            self.dataproc.show()

    def set_data_directory(self, data_directory, index=0):
        self.data_directories[index] = data_directory
        self.data_directory = data_directory
        self.text.setText('Log files at %s' % self.data_directory)

    

    def toggle_data_directory(self):
        index = (self.directory_index + 1) % len(self.data_directories)
        self.directory_index = index
        self.data_directory = self.data_directories[index]
        self.text.setText('Log files at %s' % self.data_directory)
        self.update_logs()




    def select_directory(self, index=0):
        d = QtWidgets.QFileDialog(caption='Select data directory')
        d.setFileMode(QFileDialog.Directory)
        if d.exec():
            datadir = d.selectedFiles()[0]
            self.set_data_directory(datadir, index)
            print('update logs')
            self.update_logs()



    def update_logs(self):
        ''' Update the list of measurements 
        TODO: 
            - parallel thread with loading progress
            - save loaded infor to local file
    
        '''
        model = self._treemodel

        model.clear()
        model.setHorizontalHeaderLabels(
            ['#','Log', 'Setpoints', 'Outputs', 'Comments', 'DatabaseDir', 'Experiment'])


        self.databases = db_comms.get_databases(self.data_directory)
        self.pointer_ds = dict()

        for db in self.databases:
            print(db)
            if 'filelist.txt' in os.listdir(os.path.dirname(str(db))):
                # with open('filelist.txt','r') as f:
                # n_runs_in_list = f.read()

                print('here')
            else:

                self._current_db_conn = qcodes.dataset.connect(db) # to speedup the retrieval of data
                experiments, exp_dates = db_comms.get_experiments_from_db(db)

                print(exp_dates)
                for experiment, expdate in zip(experiments, exp_dates):
                    parent = QtGui.QStandardItem(expdate)
                    
                    n_runs = experiment.last_counter
                    # ds = []
                    # ds_time = []
                    for _run_id in reversed(range(n_runs)):
                    # for _run_id in range(n_runs):    
                        
                        _dataset, datasettime = db_comms.get_ds_from_experiment(experiment,_run_id)
                        
                        ds_parameters = db_comms.get_parameters_from_ds(_dataset)
                        setpoints_names, outputs_names = db_comms.get_parameter_dependencies(ds_parameters)
                        
                        setpoints_names_str = ''.join(str(s)+', ' for s in setpoints_names)
                        outputs_names_str = ''.join(str(s)+', ' for s in outputs_names)
                        comments = '' # TODO: how to store and retrieve comments fom ds?

                        item_runid = QtGui.QStandardItem(str(_run_id))
                        item_dstime = QtGui.QStandardItem(str(datasettime))
                        item_setp = QtGui.QStandardItem(str(setpoints_names_str))
                        item_outp = QtGui.QStandardItem(str(outputs_names_str))
                        item_comms = QtGui.QStandardItem(str(comments))
                        item_dbdir = QtGui.QStandardItem(str(db))
                        item_expid = QtGui.QStandardItem(str(experiment.exp_id))

                        child = [item_runid, item_dstime, item_setp, item_outp, item_comms, item_dbdir, item_expid]

                        with open('filelist.txt','w') as f:
                            f.write(str(child)+'\n')

                        # TODO: shows preview of data on hover
                        # thumbloc = os.path.join(os.path.split(filename)[0], 'thumbs', 'thumb.jpg')
                        # for item in child:
                        #     item.setToolTip('<img src="%s", width=300>' % (thumbloc))
                        
                        parent.appendRow(child)
                    # parent.sortChildren(0,QtCore.Qt.DescendingOrder)
                    model.appendRow(parent)

        self.logtree.setColumnWidth(0, 120)

        return


    def filter_fixed_parameters(self,dataset,parameter):
        data_dict = dataset.to_xarray_dataarray_dict()
        parameter_array = data_dict[parameter].to_numpy()
        all_equal = np.allclose(parameter_array,parameter_array[0])
        
        return all_equal

    def log_callback(self, index):
        """ Function called when a log entry is selected """

        logging.info('logCallback: index %s' % str(index))

        loadinfo_dict = {}

        pp = index.parent()
        row = index.row()

        run_id = int(index.sibling(row,0).data())
        db_path = index.sibling(row,5).data()
        exp_id = int(index.sibling(row,6).data())

        data_dict = self.load_data_from_db(db_path,exp_id,run_id) 

        self.data_label = index.parent().data()+'_'+str(index.sibling(row,1).data())
        # data_dict = data_dict.to_xarray_dataarray_dict()
        # test using: currind = stationgui.dataviewer.logtree.currentIndex()
        # test using: data = stationgui.dataviewer.load_data_from_db(currind.sibling(currind.row(),5).data(),int(currind.sibling(currind.row(),6).data()),int(currind.sibling(currind.row(),0).data()))



        self.outps = []
        setps = []
        pars_fixed = []
        val_fixed = []
        self.dict_fixed = {'parameter':[], 'value': []}

        self._update_plot_ = False
        self.dataproc.outCombo.clear()
        data_tmp = data_dict.to_xarray_dataarray_dict()
        self.data_xarray = data_tmp

        for param in data_dict.paramspecs:
            if not data_dict.paramspecs[param].depends_on:
                setps.append(param)
            else:
                d_tmp = data_tmp[param].to_numpy()
                # d_tmp[np.isnan(d_tmp)] = np.ma.masked
                try:
                    d_tmp[np.isnan(d_tmp)] = d_tmp[0][0]
                    test_condition = (d_tmp==d_tmp[0][0]).all()
                except:
                    d_tmp[np.isnan(d_tmp)]=d_tmp[0]
                    test_condition = (d_tmp==d_tmp[0]).all()
                if not test_condition:
                    # print(param)
                    self.outps.append(param)
                    self.numouts += 1
                    self.dataproc.outCombo.addItem(param)
                else:
                    pars_fixed.append(param) 
                    try:
                        val_fixed.append(d_tmp[0][0])
                    except:
                        val_fixed.append(d_tmp[0])

        self.dict_fixed['parameter'] = pars_fixed
        self.dict_fixed['value'] = val_fixed


        self.dataproc.outCombo.addItem('All')
        
        try:
            ind_output = self.dataproc.outCombo.findText(self.current_outputpar[0])
        except:
            ind_output = -1
        if ind_output < 0: # didn't find the output text in outCombo
            self.dataproc.outCombo.setCurrentIndex(0)
        else:
            self.dataproc.outCombo.setCurrentIndex(ind_output)

        self.setpoints = setps
        self.data_dict = data_dict
        
        self._update_plot_=True
        output=self.get_plot_outputs()

        self.update_plot_v2(data_dict,output,setps)
        self.datameta.update_meta_tabs_v2()

        return
    

    def check_fixed_parameter(self,data_array):
        
        isfixed=False
        
        return isfixed

    def get_plot_outputs(self):
        outputs = []
        if self.dataproc.outCombo.currentText()=='All':
            outputs = self.outps
        else:
            outputs.append(self.dataproc.outCombo.currentText())
            # outputs = self.dataproc.outCombo.currentText()

        return outputs

    @staticmethod
    def load_data_from_db(db_path,exp_id,run_id):
        '''
        Load data in a qcodes dataset
        '''
        db_conn = qcodes.dataset.connect(db_path)
        exp = qcodes.dataset.load_experiment(exp_id, db_conn)
        ds, _ = db_comms.get_ds_from_experiment(exp,run_id)

        # data_dict = ds.get_parameter_data()[self._output_par]
        
        return ds

    def plot_it(self,x,y,z=None, window_index = 0):
        j = window_index


        self.qplotss['windows'][j].clear()

        if z is None:

            self.qplotss['windows'][j].add(x=x, y=y,
                                            xlabel=self.X_label, ylabel=self.Y_label,
                                                xunit=self.X_unit, yunit=self.Y_unit)

            self.dataproc.freezeCmap.setEnabled(False)
            self.dataproc.getLinecut.setEnabled(False)

        else:

            self.dataproc.freezeCmap.setEnabled(True)
            self.dataproc.getLinecut.setEnabled(True)

            self.qplotss['windows'][j].add(x=y, y=x, z=z,
                                                xlabel=self.X_label, ylabel=self.Y_label, zlabel=self.Z_label,
                                                xunit=self.X_unit, yunit=self.Y_unit, zunit=self.Z_unit)


            if self.dataproc.freezeCmap.isChecked():
                self.qplotss['windows'][j].win.removeItem(
                    self.qplotss['windows'][j].traces[0]['plot_object']['hist'])
                self.setcmap(self.qplotss['windows'][j], j)
                self.qplotss['windows'][j].set_cmap(
                    self.qplotss['windows'][j].traces[0]['plot_object']['cmap'])

                self.qplotss['windows'][j].win.addItem(self.plot_hist[j])
                # self.gradstate=self.plot_hist.gradient.saveState()

                for kk in self.qplotss['windows'][j].win.items():
                    if isinstance(kk, pg.ImageItem):
                        h = kk.getHistogram()
                        self.plot_hist[j].plot.setData(*h)
                        self.plot_hist[j].gradient.restoreState(
                            self.gradstate[j])
                        # self.plot_hist.gradient.sigGradientChanged.connect(self.plot_hist.gradient.saveState)
                        self.plot_hist[j].imageItem = weakref.ref(kk)
                        kk.sigImageChanged.connect(
                            self.plot_hist[j].imageChanged)
                        kk.setLookupTable(self.plot_hist[j].getLookupTable)
                        # self.plot_hist[j].gradientChanged()
                        self.plot_hist[j].regionChanged()
                        self.plot_hist[j].imageChanged(autoLevel=False)

                self.qplotss['windows'][j].update_plot()





    def update_plot_v2(self,dataset,output,setpoints):
        '''
        Update data plot from data_dict retrieved from qcodes db
        '''


        ###################### create QTplot windows 


        self.current_outputpar = output
        # self.current_ouputindex = self.dataproc.outCombo.currentIndex()

        if self.dataproc.outCombo.currentText() == 'All':
            numwindows = self.dataproc.outCombo.currentIndex()
            startplot = 0
        else:
            numwindows = 1 
            startplot = 0 

        try:
            self.qplotss['positions'][numwindows]
        except:
            windowsneeded = numwindows-len(self.qplotss['positions'])+1
            for kk in range(windowsneeded):
                self.qplotss['positions'].append(self.qplotss['positions'][0])
            # print(self.qplotss['positions'])

        if len(self.qplotss['windows']) < (numwindows):
            start = len(self.qplotss['windows'])
            for i in range(numwindows-len(self.qplotss['windows'])):
                self.qplotss['windows'].append(QtPlot(figsize=self.qplotss['positions'][i+start][0:2],
                                                      fig_x_position=self.qplotss['positions'][i+start][2],
                                                      fig_y_position=self.qplotss['positions'][i+start][3], remote=False, window_title=self.dataproc.outCombo.itemText(i+start)))

        try:
            self.data_plots
        except:
            self.data_plots = [[] for i in range(len(self.qplotss['windows']))]

        j = 0
        while j < numwindows:
            j += startplot
            # if np.size(output) == 1:
            #     outpar = output[0]
            # else:
            #     outpar = output[j-startplot]

            # print(outpar)
            # outpar = 'keith1_Idc1'

            if not self.qplotss['windows'][j].win.isVisible():
                self.qplotss['windows'][j].__init__(figsize=self.qplotss['positions'][j][0:2],
                                                    fig_x_position=self.qplotss['positions'][j][2],
                                                    fig_y_position=self.qplotss['positions'][j][3], remote=False, window_title=self.dataproc.outCombo.itemText(j))

            self.qplotss['windows'][j].clear()

            ############################################
            

            dataset = dataset.to_xarray_dataarray_dict()



            ######################## Plot data in QTplot windows

            for outpar in output:
                # print(outpar)

                # print(dataset[outpar])
                x_xarray = getattr(dataset[outpar],setpoints[0])
                x = x_xarray.to_numpy()

                nanarray = ~(np.isnan(x))
                self.nanvalues = nanarray

                __array = setpoints

                if len(__array) == 1:

                    x = x[nanarray]
                    y_xarray = dataset[outpar]
                    y = y_xarray.to_numpy()[nanarray]
                    self.X_label = x_xarray.name
                    self.X_unit = x_xarray.unit
                    self.Y_label = y_xarray.name
                    self.Y_unit = y_xarray.unit

                    self.X = x
                    self.Y = y

                    self.Z = None
                    self.Z_label = ''
                    self.Z_unit = ''

                    self.plot_it(x,y,window_index = j)

                elif len(__array) == 2:

                    Y_xarray = getattr(dataset[outpar],setpoints[0])
                    Y = Y_xarray.to_numpy()
                    self.Y = Y
                    self.X_label = Y_xarray.name
                    self.X_unit = Y_xarray.unit

                    X_xarray = getattr(dataset[outpar],setpoints[1])
                    X = X_xarray.to_numpy()

                    self.X = X
                    self.Y_label = X_xarray.name
                    self.Y_unit = X_xarray.unit

                    Z_xarray = dataset[outpar]
                    Z = Z_xarray.to_numpy()
                    Z = np.flip(np.rot90(Z), 0) # Z

                    self.Z = Z
                    self.Z_label = Z_xarray.name
                    self.Z_unit = Z_xarray.unit

                    self.plot_it(X,Y,Z, window_index = j)


                j += 1

                self.dataproc.getCoord.setChecked(False)
                self.dataproc.getLinecut.setChecked(False)




    def selected_data_file(self):
        """ Return currently selected data file """
        return self.datatag
    

    def refreshdata(self):
        self.log_callback(self.logtree.currentIndex())



    def get_plot_parameter(self):
        ''' Return parameter to be plotted '''
        param_name = self.dataproc.outCombo.currentText()
        if param_name is not '':
            return param_name
        parameters = self.dataset.arrays.keys()
        if self.default_parameter in parameters:
            return self.default_parameter
        return self.dataset.default_parameter_name()


    
    ## ---- MOVE to dataviewprocess.py
    def combobox_callback(self):
        if not self._update_plot_:  # block calling of this function while updating outCombo contents
            return
        self.current_outputpar[0]=self.dataproc.outCombo.currentText()
        self.log_callback(self.logtree.currentIndex())
        #     self.functionsqueue_callback(self.fqueue, self.dataset)


# ----------- method do handle functions queue
    
    def functionsqueue_callback(self, fqueue, data):
        self.fqueue = fqueue
        if not self._update_plot_:  # block calling of this function while updating processCombo contents
            return
        
        metadata = {
                    'Xlabel': self.X_label,
                    'Xunit': self.X_unit,
                    'Ylabel': self.Y_label,
                    'Yunit': self.Y_unit,
                    'Zlabel': self.Z_label,
                    'Zunit': self.Z_unit
                }
        
        if self.data_dict is not None:
            if self.dataproc.outCombo.currentText() == 'All':
                # outpars = [self.dataproc.outCombo.itemText(
                #     i) for i in range(0, self.dataproc.outCombo.count()-1)]
                # parname = []
                # for ps in outpars:  # process each output
                #     # self.dataset = self.data_xarray
                #     # self.dataset = procstyles.processStyle_queue(
                #     #     self.fqueue, self.dataset, ps)
                #     processed_data = procstyles.processStyle_queue(self.fqueue, self.X, self.Y, self.Z)
                #     # parname.append(ps+'_proc_')
                # self.plot_it()
                # # self.update_plot(parname)
                # self.update_plot_v2(parname)
                # for psproc in parname:  # remove each output
                    # remove_array_clean(self.dataset, psproc)
                print('not implemented')
            else:

                processed_data = procstyles.processStyle_queue(self.fqueue, self.X, self.Y, self.Z,metadata)
                
                if self.Z is None:
                    X = processed_data['xdata']
                    Y = processed_data['ydata']
                else:
                    X = processed_data['xdata'][0]
                    Y = processed_data['xdata'][1]
                    Z = processed_data['ydata']
                
                self.plot_it(X,Y,Z)
                
# -----------



    def get_datamap(self):

        ds = self.dataproc.outCombo.currentText()
        if np.shape(getattr(self.dataset, ds).set_arrays)[0] == 1:
            x_array = getattr(self.dataset, ds).set_arrays[0][self.nanvalues]
            y_array = getattr(self.dataset, ds).ndarray[self.nanvalues]

            x_name = getattr(self.dataset, ds).set_arrays[0].name

            return x_array, y_array, x_name

        elif np.shape(getattr(self.dataset, ds).set_arrays)[0] == 2:
            x_array = getattr(self.dataset, ds).set_arrays[0][self.nanvalues]
            y_array = self.X
            z_array = np.flip(np.rot90(self.Z), 0)

            x_name = getattr(self.dataset, ds).set_arrays[0][self.nanvalues]
            y_name = getattr(self.dataset, ds).set_arrays[1].name

            return x_array, y_array, z_array, x_name, y_name



    def create_thumbnail(self):

        location = os.path.split(self.filename)[0]
        location = os.path.join(location, 'thumbs')
        thumbfile = os.path.join(location, 'thumb.jpg')

        try:
            os.mkdir(location)
        except:
            pass

        QApplication.processEvents()
        exporter = ImageExporter(
            self.qplotss['windows'][0].win.scene())
        exporter.export(thumbfile)



    def toggle_procWindow(self):
        if self.dataproc.processWindow.isChecked():
            try:
                self.datafuncs.show()
            except:
                self.datafuncs = DataFuncs(self)
                self.datafuncs.show()
        else:
            self.datafuncs.hide()

# get colormap

    
    ## ---- MOVE to dataviewprocess.py
    def toggle_cmap(self):
        if self.dataproc.freezeCmap.isChecked():
            self.plot_hist = []
            self.gradstate = []
            self.plot_cmap = []
            for fig in self.qplotss['windows']:
                self.getcmap(fig)
        else:
            self.refreshdata()

    def getcmap(self, fig):

        self.plot_hist.append(fig.traces[0]['plot_object']['hist'])
        self.gradstate.append(
            fig.traces[0]['plot_object']['hist'].gradient.saveState())
        self.plot_cmap.append(fig.traces[0]['plot_object']['cmap'])

    def setcmap(self, fig, index):
        fig.traces[0]['plot_object']['hist'] = self.plot_hist[index]
        fig.traces[0]['plot_object']['cmap'] = self.plot_cmap[index]


# get coordinates

    ## ---- MOVE to dataviewprocess.py
    def toggle_getcoord(self):
        if self.dataproc.getCoord.isChecked():
            if self.dataproc.outCombo.currentText() == 'All':
                for i in range(len(self.qplotss['windows'])):
                    self._enablecoord(i)
            else:
                indp = self.dataproc.outCombo.currentIndex()
                if indp > len(self.qplotss['windows']):
                    indp = 0
                self._enablecoord(indp)
        else:
            self._disablecoord()

    def _disablecoord(self):
        try:
            for indp in range(len(self.pplot)):

                self.pplot[indp].removeItem(self.hLine[indp])
                self.pplot[indp].removeItem(self.vLine[indp])
                self.pplot[indp].removeItem(self.label[indp])
                self.pplot[indp].unsetCursor()
                self.pplot[indp].scene().sigMouseMoved.disconnect()

        except:
            pass

        if self.dataproc.getLinecut.isChecked():
            self._enable_linecut()

    def _enablecoord(self, indp):
        try:
            self.label[indp]
        except:
            self.label.append([])

        try:
            self.hLine[indp]
        except:
            self.hLine.append([])

        try:
            self.vLine[indp]
            self._disablecoord(indp)
        except:
            self.vLine.append([])

        try:
            self.pplot[indp]
            # self.glayout[indp]
        except:
            self.pplot.append([])
            # self.glayout.append([])

        movemouse = np.zeros(len(self.qplotss['windows']))

        for kk in self.qplotss['windows'][indp].win.items():
            # print(kk)
            if isinstance(kk, pg.PlotItem):
                self.pplot[indp] = kk

        self.label[indp] = pg.TextItem(
            "", color=(255, 255, 255), fill=(0, 0, 0))
        self.label[indp].setOpacity(0.6)
        self.pplot[indp].addItem(self.label[indp], ignoreBounds=True)

        self.pplot[indp].setAutoVisible(y=True)

        self.vLine[indp] = pg.InfiniteLine(angle=90, movable=False)
        self.hLine[indp] = pg.InfiniteLine(angle=0, movable=False)

        self.pplot[indp].addItem(self.vLine[indp], ignoreBounds=True)
        self.pplot[indp].addItem(self.hLine[indp], ignoreBounds=True)

        self.pplot[indp].scene().sigMouseMoved.connect(
            lambda pos: mouseMoved(pos, ind=indp))

        def mouseMoved(evt, ind=[]):
            pos = evt  # using signal proxy turns original arguments into a tuple
            vb = self.pplot[ind].vb
            sx, sy = vb.viewPixelSize()
            self.pplot[ind].setCursor(QtCore.Qt.BlankCursor)

            if self.pplot[ind].sceneBoundingRect().contains(pos):
                mousePoint = vb.mapSceneToView(pos)
                index_x = mousePoint.x()
                index_y = mousePoint.y()

                # if len(self.data_plots[ind].set_arrays) == 1:
                if len(self.setpoints) == 1:
                    self.label[ind].setText(
                        "x=%0.1f \r y=%f" % (index_x, index_y))
                else:
                    # self.label[ind].setText("x=%0.1f \r y=%0.1f \r z=%E" % (
                    #     index_x, index_y, get_z(index_y, index_x, self.data_plots[ind])))
                    outpar = self.dataproc.outCombo.currentText()
                    data = self.data_xarray[outpar]
                    self.label[ind].setText("x=%0.1f \r y=%0.1f \r z=%E" % (index_x, index_y, get_z(index_y, index_x, data)))

                br = self.label[ind].boundingRect()
                xscalerange = 0.98
                yscalerange = 0.95

                if mousePoint.x() < vb.viewRange()[0][1]*xscalerange-sx*br.width() and mousePoint.y() > vb.viewRange()[1][0]*yscalerange+sy*br.height():
                    self.label[ind].setPos(mousePoint.x(), mousePoint.y())
                elif mousePoint.x() > vb.viewRange()[0][1]*xscalerange-sx*br.width() and mousePoint.y() > vb.viewRange()[1][0]*yscalerange+sy*br.height():
                    self.label[ind].setPos(
                        mousePoint.x()-sx*br.width(), mousePoint.y())
                elif mousePoint.x() < vb.viewRange()[0][1]*xscalerange-sx*br.width() and mousePoint.y() < vb.viewRange()[1][0]*yscalerange+sy*br.height():
                    self.label[ind].setPos(
                        mousePoint.x(), mousePoint.y()+sy*br.height())
                else:
                    self.label[ind].setPos(
                        mousePoint.x()-sx*br.width(), mousePoint.y()+sy*br.height())

                self.vLine[ind].setPos(mousePoint.x())
                self.hLine[ind].setPos(mousePoint.y())

        def get_z(x, y, Z):
            try:
                indx_fine, indy_fine = plot_tools.get_indices_qcodes(Z, x, y)
                z = Z[indy_fine][indx_fine]

                return z

            except:
                return float('nan')

    def findItems(self, Layout, rangeind):
        prow = []
        pcol = []
        for rrow in range(0, rangeind):
            for ccol in range(0, rangeind):
                print(str(rrow)+' '+str(ccol))
                print(Layout.getItem(rrow, ccol))
                if Layout.getItem(rrow, ccol) != None:
                    prow.append(rrow)
                    pcol.append(ccol)

        return prow, pcol


# linecuts

    ## ---- MOVE to dataviewprocess.py
    def toggle_linecut(self):
        if self.dataproc.getLinecut.isChecked():
            if self.dataproc.outCombo.currentText() == 'All':
                for i in range(len(self.qplotss['windows'])):
                    self._enable_linecut(i)
            else:
                indp = self.dataproc.outCombo.currentIndex()
                if indp > len(self.qplotss['windows']):
                    indp = 0
                self._enable_linecut(indp)
        else:
            self._disable_linecut()

    def _disable_linecut(self):

        try:
            for indp in range(len(self.pplot)):
                self.pplot[indp].removeItem(self.hLine_cut[indp])
                self.pplot[indp].removeItem(self.vLine_cut[indp])
                self.pplot[indp].scene().sigMouseMoved.disconnect()
                self.pplot[indp].scene().sigMouseClicked.disconnect()

        except:
            pass

    def _enable_linecut(self, indp):
        try:
            self.pplot[indp]
        except:
            self.pplot.append([])

        try:
            self.vLine_cut[indp]
        except:
            self.vLine_cut.append([])
        try:
            self.hLine_cut[indp]
        except:
            self.hLine_cut.append([])

        self.plot_linecuts = []

        self.cutdir = 0

        for kk in self.qplotss['windows'][indp].win.items():
            if isinstance(kk, pg.PlotItem):
                self.pplot[indp] = kk

        self.vLine_cut[indp] = pg.InfiniteLine(angle=90, movable=False)
        self.hLine_cut[indp] = pg.InfiniteLine(angle=0, movable=False)
        self.pplot[indp].addItem(self.hLine_cut[indp], ignoreBounds=True)

        self.pplot[indp].scene().sigMouseMoved.connect(
            lambda pos: mouseMoved(pos, ind=indp))
        self.pplot[indp].scene().sigMouseClicked.connect(
            lambda event: mouseCut(event, ind=indp))

        def mouseMoved(evt, ind=[]):
            # print(evt)
            pos = evt  # using signal proxy turns original arguments into a tuple
            vb = self.pplot[ind].vb

            if self.pplot[ind].sceneBoundingRect().contains(pos):
                mousePoint = vb.mapSceneToView(pos)

                if self.cutdir == 1:
                    self.vLine_cut[ind].setPos(mousePoint.x())
                elif self.cutdir == 0:
                    self.hLine_cut[ind].setPos(mousePoint.y())
            return pos

        def mouseCut(evt, ind=[]):
            pos = evt.scenePos()  # using signal proxy turns original arguments into a tuple
            vb = self.pplot[ind].vb

            # if evt.button() == QtCore.Qt.LeftButton:
            if evt.modifiers() == QtCore.Qt.ControlModifier:
                # print('pressed Ctrl')
                if self.cutdir == 0:
                    self.cutdir = 1  # set to cut along x-axis
                    self.pplot[ind].removeItem(self.hLine_cut[ind])
                    self.pplot[ind].addItem(
                        self.vLine_cut[ind], ignoreBounds=True)
                elif self.cutdir == 1:
                    self.cutdir = 0  # set to cut along y-axis
                    self.pplot[ind].removeItem(self.vLine_cut[ind])
                    self.pplot[ind].addItem(
                        self.hLine_cut[ind], ignoreBounds=True)

            # print(self.cutdir)

            if self.pplot[ind].sceneBoundingRect().contains(pos):
                mousePoint = vb.mapSceneToView(pos)

                valx = mousePoint.x()
                valy = mousePoint.y()
                # x, y = get_cut(self.data_plots[ind], self.cutdir, valy, valx)
                outpar = self.dataproc.outCombo.currentText()
                x, y = get_cut(self.data_xarray[outpar], self.cutdir, valy, valx)

                if self.plot_linecuts:
                    self.plot_linecuts[0].clear()
                else:
                    self.plot_linecuts.append(pg.GraphicsLayoutWidget()) #GraphicsWindow())
                    self.plot_linecuts[0].show()
                if self.cutdir == 1:
                    self.plot_linecuts[0].setWindowTitle(
                        'Line cut at x ='+str(valx))
                elif self.cutdir == 0:
                    self.plot_linecuts[0].setWindowTitle(
                        'Line cut at y ='+str(valy))

                p1 = self.plot_linecuts[0].addPlot(row=0, col=0)
                p1.plot(x=x, y=y, pen="r")

        def get_cut(Z, dir_ind, x, y):

            # indx_fine, indy_fine = plot_tools.get_indices(Z, x, y)

            indx_fine, indy_fine = plot_tools.get_indices_qcodes(Z, x, y)

            # nanarray_y = ~(np.isnan(Z.set_arrays[0]))
            _y = Z[self.setpoints[0]].to_numpy()
            _x = Z[self.setpoints[1]].to_numpy()
            nanarray_y = ~(np.isnan(_y))

            y_array = _y[nanarray_y]
            y_numel = len(_y[nanarray_y])
            y_span = _y[y_numel-1]-_y[0]


            nanarray_x=~(np.isnan(_x[indy_fine]))

            x_array=_x[nanarray_x][0]
            x_numel=len(_x)
            x_span=_x[x_numel-1]-_x[0]

            # nanarray_x = ~(np.isnan(_x[indy_fine]))

            # x_array = _x[indy_fine][nanarray_x]
            # x_numel = len(_x[indy_fine][nanarray_x])
            # x_span = _x[indy_fine][x_numel-1] - _x[indy_fine][0]

            if dir_ind == 0:  # y direction
                x = y_array  # Z.set_arrays[dir_ind-1]
                y = []

                if _x[0] != _x[1]:
                    if indy_fine % 2 != 0:
                        indx_fine = x_numel-indx_fine
                    for kk, indkk in zip(Z, range(len(x))):
                        if indkk % 2 == 0:
                            y.append(kk[indx_fine])
                        else:
                            y.append(kk[x_numel-indx_fine])
                else:
                    for kk in Z:
                        y.append(kk[indx_fine])

                if np.isnan(y[len(y)-1]):
                    y = y[:-1]
                    x = x[:-1]

            elif dir_ind == 1:  # x direction
                x = x_array  # Z.set_arrays[dir_ind+1][indy_fine]
                y = Z[indy_fine][nanarray_x]

            return x, y
        


    def tojpg_callback(self):
        dirname = QFileDialog.getExistingDirectory(
            self, 'Save plots to directory...', 'C:\\')
        if dirname:
            for fig, index in zip(self.qplotss['windows'], range(len(self.qplotss['windows']))):
                fname = self.data_label+'_'+str(index)+'.jpg'
                # fname = self.selected_data_file().replace('\\', '_')+'_'+str(index)+'.jpg'
                # fname=self.datatag.replace('\\','_')+'_'+str(index)+'.jpg'
                if os.path.exists(os.path.join(dirname, fname)):
                    fname = fname[:-4]+'_copy.jpg'
                fig.save(filename=os.path.join(dirname, fname))
        else:
            print('No destination folder selected')

    

# %% Run the GUI as a standalone program

if __name__ == '__main__':
    import sys
    
    # def start_threads(worker):

    
    if len(sys.argv) < 2:
        sys.argv += ['-d', os.path.join(os.path.expanduser('~'),
                                        'tmp', 'qdata')]

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', default=1, help="verbosity level")
    parser.add_argument(
        '-d', '--datadir', type=str, default=None, help="data directory")
    args = parser.parse_args()
    verbose = args.verbose
    datadir = args.datadir

    # app = pg.mkQApp()
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # debugpy.debug_this_thread()

    # worker = DataViewer()
    # datadir='C:\qtNE_dbs_2021\Antonio'
    dataviewer = DataViewer(data_directory=datadir, extensions=['dat', 'hdf5'])

    # __thr = start_threads(dataviewer)

    dataviewer.verbose = 5
    dataviewer.logtree.setColumnWidth(0, 240)
    
    dataviewer.show()
    app.exec_()
    # sys.exit(app.exec())



    # def load_info(self):
    #     try:
    #         for row in range(self._treemodel.rowCount()):
    #             index = self._treemodel.index(row, 0)
    #             pp = index.parent()

    #             i = 0
    #             while (index.child(i, 0).data() is not None):
    #                 filename = index.child(i, 3).data()
    #                 loc = '\\'.join(filename.split('\\')[:-1])
    #                 try:
    #                     tempdata = qcodes.DataSet(loc)
    #                 except:
    #                     tempdata = data_set.DataSet(loc)
    #                 tempdata.read_metadata()
    #                 looptxt, outputtxt, sampletxt, commenttxt = DataViewer.get_data_info(
    #                     tempdata.metadata)datatag

    #                 # self._treemodel.setData(pp.child(row, 0), index)
    #                 # self._treemodel.setData(pp.child(row, 1), sampletxt)
    #                 # self._treemodel.setData(pp.child(row, 4), looptxt)
    #                 # self._treemodel.setData(pp.child(row, 5), outputtxt)
    #                 # self._treemodel.setData(pp.child(row, 6), commenttxt)
    #                 # self._treemodel.setData(pp.child(row, 2), sampletxt)
    #                 # self._treemodel.setData(pp.child(row, 5), looptxt)
    #                 # self._treemodel.setData(pp.child(row, 6), outputtxt)
    #                 # self._treemodel.setData(pp.child(row, 7), commenttxt)
    #                 self._treemodel.setData(index.sibling(row, 2), sampletxt)
    #                 self._treemodel.setData(index.sibling(row, 5), looptxt)
    #                 self._treemodel.setData(index.sibling(row, 6), outputtxt)
    #                 self._treemodel.setData(index.sibling(row, 7), commenttxt)


    #                 i = i + 1
    #     except Exception as e:
    #         print(e)




            # tag = index.sibling(row, 3).data()  # hidden column for PyQt6
        # filename = index.sibling(row, 4).data()  # hidden column, for PyQt6
        # self.filename = filename
        # self.datatag = tag

        # if tag is None:
        #     return
        # if self.verbose >= 2:
        #     print('DataViewer logCallback: tag %s, filename %s' %
        #           (tag, filename))
        # try:
        #     logging.debug('DataViewer: load tag %s' % tag)
        #     data = DataViewer.load_data(filename, tag)
        #     # print(data)
        #     if not data:
        #         # raise ValueError('File invalid (%s) ...' % filename)
        #         data = load_data_generic(filename)
        #     self.dataset = data

            # self.datameta.update_meta_tabs()
            # self.datameta.update_implicit_gates()
            # try:
            #     self.datameta.meta_tabs.setCurrentIndex(1)
            # except:
            #     pass

            # data_keys = data.arrays.keys()

            # looptxt, outputtxt, sampletxt, commenttxt = DataViewer.get_data_info(
            #     data.metadata)
            # q = index.sibling(row, 1).model()
            # q.setData(index.sibling(row, 2), sampletxt)
            # q.setData(index.sibling(row, 5), looptxt)
            # q.setData(index.sibling(row, 6), outputtxt)
            # q.setData(index.sibling(row, 7), commenttxt)

            # self.reset_combo_items(data, data_keys)
            # self.functionsqueue_callback(self.fqueue, data)
            # self.create_thumbnail()
            #
            # self.sx, self.sy = self.get_datamap()
            #
            ##
        # except Exception as e:
        #     print('logCallback! error: %s' % str(e))
        #     logging.exception(e)

    def reset_combo_items(self, data, keys):
        old_key = self.dataproc.outCombo.currentText()
        # block comboboxes callbacks while updating outCombo contents
        self._update_plot_ = False
        self.dataproc.outCombo.clear()
        for key in keys:
            if not getattr(data, key).is_setpoint and (getattr(data, key).array_id.find('_cb') == -1 and getattr(data, key).array_id.find('_fix') == -1):
                self.numouts += 1
                self.dataproc.outCombo.addItem(key)
        self.dataproc.outCombo.addItem('All')
        if old_key in keys:
            self.dataproc.outCombo.setCurrentIndex(
                self.dataproc.outCombo.findText(old_key))
        elif old_key == 'All':
            self.dataproc.outCombo.setCurrentIndex(
                self.dataproc.outCombo.findText(old_key))

        self._update_plot_ = True
        return