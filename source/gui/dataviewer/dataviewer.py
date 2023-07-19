# %% Load packages


import numpy as np
import argparse
import logging
import os
import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
from pyqtgraph.exporters import ImageExporter


import PyQt6.QtGui as QtGui
# import PyQt6.QtWidgets as QtWidgets
from PyQt6.QtWidgets import QFileDialog, QWidget, QApplication
# import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
# from qtpy.QtWidgets import QFileDialog, QWidget

import qcodes

# from source.gui.helpers.pyqtgraph import QtPlot
# from qcodes.plots.pyqtgraph import QtPlot
from source.gui.helpers.pyqtgraph_helper.pyqtgraph import QtPlot


try:
    from source.gui.helpers import procstyles as procstyles
except:
    pathit=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
    print(pathit)
    sys.path.append(pathit) # TO DO: make universal to source
    from source.gui.helpers import procstyles as procstyles

from source.measurements.data_set_tools import remove_array_clean as remove_array_clean
from source.measurements.data_set_tools import load_data_generic as load_data_generic

from source.gui.helpers import export_tools
from source.gui.helpers import plot_tools
from source.gui.helpers import misc
# from source.gui.helpers import data_set
from qcodes.data import data_set

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

from datetime import datetime

# import debugpy
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

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
        # self.logtree.doubleClicked.connect(self.log_callback)
        self.logtree.clicked.connect(lambda: self.log_callback(
            self.logtree.currentIndex()))  # self.log_callback)
        self.logtree.selectionModel().selectionChanged.connect(
            lambda: self.log_callback(self.logtree.currentIndex()))
        self.filterbutton.clicked.connect(
            lambda: self.update_logs(filter_str=self.filtertext.text()))

        menuBar = self.menuBar()

        menuDict = {
            '&Data': {'&Reload Data': self.update_logs,
                      '&Preload all Info': self.load_info,
                      '&Quit': self.close},
            '&Folder': {'&Select Dir1': lambda: self.select_directory(index=0),
                        'Select &Dir2': lambda: self.select_directory(index=1),
                        '&Toggle Dirs': self.toggle_data_directory
                        },
            '&View': {'&Metadata Viewer': self.show_metadata,
                      'Data &Control': self.show_datacontrols
                      },
            '&Help': {'&Info': self.show_help}
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

        self.logtree.setColumnHidden(2, True)
        self.logtree.setColumnHidden(3, True)
        self.show()

        

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



    def show_metadata(self):
        if not self.datameta.isVisible():
            self.datameta.show()

    def show_datacontrols(self):
        if not self.dataproc.isVisible():
            self.dataproc.show()

    def set_data_directory(self, data_directory, index=0):
        self.data_directories[index] = data_directory
        self.data_directory = data_directory
        # try:
        #     self.disk_io = qcodes.DiskIO(data_directory)
        # except:
        #     self.disk_io = qcodes.data.io.DiskIO(data_directory)
        logging.info('DataViewer: data directory %s' % data_directory)
        self.text.setText('Log files at %s' % self.data_directory)

    def show_help(self):
        """ Show help dialog """
        self.infotext = "Dataviewer and processor for .csv data files"
        QtWidgets.QMessageBox.information(
            self, 'qtNE dataviwer control info', self.infotext)

    def toggle_data_directory(self):
        index = (self.directory_index + 1) % len(self.data_directories)
        self.directory_index = index
        self.data_directory = self.data_directories[index]
        # try:
        #     self.disk_io = qcodes.DiskIO(self.data_directory)
        # except:
        #     self.disk_io = qcodes.data.io.DiskIO(self.data_directory)
        logging.info('DataViewer: data directory %s' % self.data_directory)
        self.text.setText('Log files at %s' % self.data_directory)
        self.update_logs()

    def ppt_callback(self):
        if self.dataset is None:
            print('no data selected')
            return
        for fig in self.qplotss['windows']:
            export_tools.addPPT_dataset(self.dataset, customfig=fig)

    def tojpg_callback(self):
        if self.dataset is None:
            print('no data selected')
            return

        dirname = QFileDialog.getExistingDirectory(
            self, 'Save plots to directory...', 'C:\\')
        if dirname:
            for fig, index in zip(self.qplotss['windows'], range(len(self.qplotss['windows']))):
                fname = self.selected_data_file().replace('\\', '_')+'_'+str(index)+'.jpg'
                # fname=self.datatag.replace('\\','_')+'_'+str(index)+'.jpg'
                if os.path.exists(os.path.join(dirname, fname)):
                    fname = fname[:-4]+'_copy.jpg'
                fig.save(filename=os.path.join(dirname, fname))
        else:
            print('No destination folder selected')

    def jupyter_callback(self):

        from source.gui.helpers import jupyter_helper

        path_jupyternbs = os.path.join(self.data_directory,'jupyter_nbs')

        if not os.path.isdir(path_jupyternbs):
            os.mkdir(path_jupyternbs)

        jupyter_helper.create_qcodes_nb(self.logtree.currentIndex(),self.data_directory,save_path = path_jupyternbs)

        return




    def tojpg_tmp(self):
        if self.dataset is None:
            print('no data selected')
            return
        dirname = self.tmp_directory
        for fig, index in zip(self.qplotss['windows'], range(len(self.qplotss['windows']))):
            fname = self.datatag.replace('\\', '_')+'_'+str(index)+'.jpg'
            if os.path.exists(os.path.join(dirname, fname)):
                fname = fname[:-4]+'_copy.jpg'
            fig.save(filename=os.path.join(dirname, fname))

        return os.path.join(dirname, fname)

    @staticmethod
    def get_data_info(metadata):
        params = []
        try:
            if 'loop_specs' in metadata.keys():
                sv = metadata['loop_specs']

                outputs = sv['output_id']
                outputtxt = str(outputs).strip('[]')

                sweep = sv['sweep_id']
                try:
                    step = sv['step_id']
                    looptxt = str(step).strip('[]')+', '+str(sweep).strip('[]')
                except:
                    looptxt = str(sweep).strip('[]')
            else:
                outputtxt = 'No info available'
                looptxt = 'No info available'

            if 'sample' in metadata.keys():
                sampletxt = metadata['sample']
            else:
                sampletxt = 'No name'

            if 'comments' in metadata.keys():
                commenttxt = metadata['comments']
            else:
                commenttxt = ''

        except BaseException:
            outputtxt = 'None'
            looptxt = 'None'
            sampletxt = 'None'
            commenttxt = 'None'

        return looptxt, outputtxt, sampletxt, commenttxt

    def load_info(self):
        try:
            for row in range(self._treemodel.rowCount()):
                index = self._treemodel.index(row, 0)
                pp = index.parent()

                i = 0
                while (index.child(i, 0).data() is not None):
                    filename = index.child(i, 3).data()
                    loc = '\\'.join(filename.split('\\')[:-1])
                    try:
                        tempdata = qcodes.DataSet(loc)
                    except:
                        tempdata = data_set.DataSet(loc)
                    tempdata.read_metadata()
                    looptxt, outputtxt, sampletxt, commenttxt = DataViewer.get_data_info(
                        tempdata.metadata)

                    # self._treemodel.setData(pp.child(row, 0), index)
                    # self._treemodel.setData(pp.child(row, 1), sampletxt)
                    # self._treemodel.setData(pp.child(row, 4), looptxt)
                    # self._treemodel.setData(pp.child(row, 5), outputtxt)
                    # self._treemodel.setData(pp.child(row, 6), commenttxt)
                    # self._treemodel.setData(pp.child(row, 2), sampletxt)
                    # self._treemodel.setData(pp.child(row, 5), looptxt)
                    # self._treemodel.setData(pp.child(row, 6), outputtxt)
                    # self._treemodel.setData(pp.child(row, 7), commenttxt)
                    self._treemodel.setData(index.sibling(row, 2), sampletxt)
                    self._treemodel.setData(index.sibling(row, 5), looptxt)
                    self._treemodel.setData(index.sibling(row, 6), outputtxt)
                    self._treemodel.setData(index.sibling(row, 7), commenttxt)


                    i = i + 1
        except Exception as e:
            print(e)

    def select_directory(self, index=0):
        d = QtWidgets.QFileDialog(caption='Select data directory')
        d.setFileMode(QFileDialog.Directory)
        if d.exec():
            datadir = d.selectedFiles()[0]
            self.set_data_directory(datadir, index)
            print('update logs')
            self.update_logs()

    @staticmethod
    def find_datafiles(datadir, extensions='dat', show_progress=True):
        """ Find all datasets in a directory with a given extension """
        if extensions is None:
            extensions = ['dat', 'hdf5']
        dd = []
        for e in extensions:
            dd += misc.findfilesR(datadir, '.*%s' %
                                           e, show_progress=show_progress)

        datafiles = sorted(dd)
        return datafiles

    @staticmethod
    def _filename2datetag(filename):
        """ Parse a filename to a date tag and base filename """
        if filename.endswith('.json'):
            datetag = filename.split(os.sep)[-1].split('_')[0]
            logtag = filename.split(os.sep)[-1][:-5]
        else:
            # other formats, assumed to be in normal form
            datetag, logtag = filename.split(os.sep)[-3:-1]
        return datetag, logtag

    @staticmethod
    def _get_db_runids(logs,datetag,cache_file):
        
        stop_index = 0 # reset index for searching db 
        i=0
        _db_ini=False
        if os.path.isfile(cache_file):
            with open(cache_file,'r') as file: #assuming that list will be reverted to make easier saving of new datafiles
                runids_raw = file.read().split("\n")
                runids_list = [int(x) for x in runids_raw[:len(runids_raw)-1]]

                runids_number = len(runids_raw)-1
        else: 
            runids_list = []
            runids_number = 0

        if len(logs[datetag])==int(runids_number):

            # runids_list.reverse()
            runids_output = runids_list

        else:
            print('Updating run ids file for '+str(datetag))
            runids_list_append=[]

            unsaved_keys = [logs[datetag][key] for key in list(logs[datetag].keys())[runids_number:]]

            for ju, logtag in enumerate(sorted(unsaved_keys, reverse=True)):
                filename = logtag #logs[datetag][logtag]
                logtag = os.path.basename(os.path.dirname(filename)) # update definition of logtag, lost when extracting keys from dictionary

                # extract file from db and ruid
                if _db_ini==False:
                    from os.path import dirname, join
                    qcodes.dataset.initialise_or_create_database_at(join(dirname(dirname(filename)),'db_'+datetag+'.db'))
                    _db_ini==True
                # print(qcodes.config.core.db_location)    
                _found=False
                i=0
                while _found==False:
                    i+=1
                    try:
                        run_data = qcodes.dataset.load_by_id(i)
                    except:
                        _found=True
                        data_run_id=0
                    date_db=datetime.strptime(run_data.run_timestamp(),"%Y-%m-%d %H:%M:%S")
                    run_data_time = date_db.strftime("%H%M%S")
                    if (run_data_time==logtag) | (run_data_time==str(int(logtag)+1)):
                        data_run_id = run_data.run_id
                        _found=True
                        stop_index=i
                    
                runids_list_append.append(data_run_id)

            runids_list.reverse()
            runids_list_append.reverse()
            runids_list.extend(runids_list_append)
            runids_list.reverse()
            runids_list.append(len(runids_list)) # appends number of files indexed
            
            with open(cache_file,'w') as file:
                file.write("\n".join(map(str,runids_list)))

            runids_output = runids_list
        
        return runids_output

    def update_logs(self, filter_str=None):
        ''' Update the list of measurements '''
        model = self._treemodel

        self.datafiles = self.find_datafiles(
            self.data_directory, self.extensions)
        dd = self.datafiles


        if filter_str:
            dd = [s for s in dd if filter_str in s]

        if self.verbose:
            print('DataViewer: found %d files' % (len(dd)))

        model.clear()
        # model.setHorizontalHeaderLabels(
        #     ['Log', 'Sample', 'location', 'filename', 'Setpoints', 'Outputs', 'Comments'])
        model.setHorizontalHeaderLabels(
            ['#','Log', 'Sample', 'location', 'filename', 'Setpoints', 'Outputs', 'Comments'])

        logs = dict()
        for _, filename in enumerate(dd):
            try:
                datetag, logtag = self._filename2datetag(filename)
                if datetag not in logs:
                    logs[datetag] = dict()
                logs[datetag][logtag] = filename
            except Exception:
                pass
        self.logs = logs

        if self.verbose >= 2:
            print('DataViewer: create gui elements')

        for i, datetag in enumerate(sorted(logs.keys())[::-1]):
            if self.verbose >= 2:
                print('DataViewer: datetag %s ' % datetag)

            cache_file=os.path.join(self.data_directory,datetag,'runids_'+str(datetag)+'.txt')
            runids_list = self._get_db_runids(logs,datetag,cache_file)
            # print(runids_list)
            # print(len(runids_list))

            parent1 = QtGui.QStandardItem(datetag)
            for j, logtag in enumerate(sorted(logs[datetag], reverse=True)):
                # print(j)
                # print(len(logs[datetag]))
                filename = logs[datetag][logtag]

                child_log = QtGui.QStandardItem(logtag)

                loc = '\\'.join(filename.split('\\')[:-1])
                try:
                    tempdata = qcodes.DataSet(loc)
                except:
                    tempdata = data_set.DataSet(loc)
                tempdata.read_metadata()
                looptxt, outputtxt, sampletxt, commenttxt = DataViewer.get_data_info(
                    tempdata.metadata)

                child_index = QtGui.QStandardItem(str(runids_list[j]))
                child_sample = QtGui.QStandardItem(sampletxt)
                child_loop = QtGui.QStandardItem(looptxt)
                child_outp = QtGui.QStandardItem(outputtxt)
                child_comment = QtGui.QStandardItem(commenttxt)

                child3 = QtGui.QStandardItem(os.path.join(datetag, logtag))
                child4 = QtGui.QStandardItem(filename)

                thumbloc = os.path.join(os.path.split(
                    filename)[0], 'thumbs', 'thumb.jpg')
                child_log.setToolTip('<img src="%s", width=300>' % (thumbloc))
                child_sample.setToolTip(
                    '<img src="%s", width=300>' % (thumbloc))
                child_loop.setToolTip('<img src="%s", width=300>' % (thumbloc))
                child_outp.setToolTip('<img src="%s", width=300>' % (thumbloc))
                child_comment.setToolTip(
                    '<img src="%s", width=300>' % (thumbloc))
                
                # parent1.appendRow(
                #     [child_log, child_sample, child3, child4, child_loop, child_outp, child_comment])
                parent1.appendRow(
                    [child_index, child_log, child_sample, child3, child4, child_loop, child_outp, child_comment])

            model.appendRow(parent1)

            self.logtree.setColumnWidth(0, 120)
            # self.logtree.setColumnHidden(2, True)
            # self.logtree.setColumnHidden(3, True)
            self.logtree.setColumnHidden(3, True)
            self.logtree.setColumnHidden(4, True)

        if self.verbose >= 2:
            print('DataViewer: update_logs done')

    def refreshdata(self):
        self.log_callback(self.logtree.currentIndex())

    def fill_item(self, item, value):
        ''' recursive population of tree structure with a dict '''

        def new_item(parent, text, val=None):
            child = QtGui.QStandardItem(text)
            self.fill_item(child, val)
            parent.appendRow(child)

        if value is None:
            return
        elif isinstance(value, dict):
            for key, val in sorted(value.items()):
                if type(val) in [str, float, int]:
                    child = [QtGui.QStandardItem(
                        str(key)), QtGui.QStandardItem(str(val))]
                    item.appendRow(child)
                else:
                    new_item(item, str(key), val)
        else:
            new_item(item, str(value))

    def get_plot_parameter(self):
        ''' Return parameter to be plotted '''
        param_name = self.dataproc.outCombo.currentText()
        if param_name is not '':
            return param_name
        parameters = self.dataset.arrays.keys()
        if self.default_parameter in parameters:
            return self.default_parameter
        return self.dataset.default_parameter_name()

    def selected_data_file(self):
        """ Return currently selected data file """
        return self.datatag

    def combobox_callback(self, index):
        if not self._update_plot_:  # block calling of this function while updating outCombo contents
            return
        if self.dataset is not None:
            self.functionsqueue_callback(self.fqueue, self.dataset)


# ----------- method do handle functions queue

    def functionsqueue_callback(self, fqueue, data):
        self.fqueue = fqueue
        if not self._update_plot_:  # block calling of this function while updating processCombo contents
            return

        if self.dataset is not None:
            if self.dataproc.outCombo.currentText() == 'All':
                outpars = [self.dataproc.outCombo.itemText(
                    i) for i in range(0, self.dataproc.outCombo.count()-1)]
                parname = []
                for ps in outpars:  # process each output
                    self.dataset = procstyles.processStyle_queue(
                        self.fqueue, self.dataset, ps)
                    parname.append(ps+'_proc_')
                self.update_plot(parname)
                for psproc in parname:  # remove each output
                    remove_array_clean(self.dataset, psproc)
            else:
                self.dataset = procstyles.processStyle_queue(
                    self.fqueue, self.dataset, self.dataproc.outCombo.currentText())
                parname = self.dataproc.outCombo.currentText()+'_proc_'
                self.update_plot(parname)
                remove_array_clean(self.dataset, parname)

# -----------

    def log_callback(self, index):
        """ Function called when a log entry is selected """

        logging.info('logCallback: index %s' % str(index))

        pp = index.parent()
        row = index.row()
        tag = index.sibling(row, 3).data()  # hidden column for PyQt6
        filename = index.sibling(row, 4).data()  # hidden column, for PyQt6
        self.filename = filename
        self.datatag = tag

        if tag is None:
            return
        if self.verbose >= 2:
            print('DataViewer logCallback: tag %s, filename %s' %
                  (tag, filename))
        try:
            logging.debug('DataViewer: load tag %s' % tag)
            data = DataViewer.load_data(filename, tag)
            # print(data)
            if not data:
                # raise ValueError('File invalid (%s) ...' % filename)
                data = load_data_generic(filename)
            self.dataset = data

            self.datameta.update_meta_tabs()
            self.datameta.update_implicit_gates()
            try:
                self.datameta.meta_tabs.setCurrentIndex(1)
            except:
                pass

            data_keys = data.arrays.keys()

            looptxt, outputtxt, sampletxt, commenttxt = DataViewer.get_data_info(
                data.metadata)
            q = index.sibling(row, 1).model()
            q.setData(index.sibling(row, 2), sampletxt)
            q.setData(index.sibling(row, 5), looptxt)
            q.setData(index.sibling(row, 6), outputtxt)
            q.setData(index.sibling(row, 7), commenttxt)

            self.reset_combo_items(data, data_keys)
            self.functionsqueue_callback(self.fqueue, data)
            self.create_thumbnail()
            #
            # self.sx, self.sy = self.get_datamap()
            #
            ##
        except Exception as e:
            print('logCallback! error: %s' % str(e))
            logging.exception(e)

        return

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

    @staticmethod
    def load_data(filename, tag):

        if filename.endswith('.json'):
            location = filename
        else:
            # qcodes datasets are found by filename, but should be loaded by directory...
            location = os.path.split(filename)[0]
        data = misc.load_dataset(location)
        return data

    def create_thumbnail(self):

        location = os.path.split(self.filename)[0]
        location = os.path.join(location, 'thumbs')
        thumbfile = os.path.join(location, 'thumb.jpg')

        try:
            os.mkdir(location)
        except:
            pass

        # needed to update window scene before creating exporter
        # pg.QtGui.QApplication.processEvents()

        QApplication.processEvents()
        exporter = ImageExporter(
            self.qplotss['windows'][0].win.scene())
        exporter.export(thumbfile)

    def update_plot(self, parameter):

        if self.dataproc.outCombo.currentText() == 'All':
            numwindows = self.dataproc.outCombo.currentIndex()
            startplot = 0
        else:
            numwindows = self.dataproc.outCombo.currentIndex()+1
            startplot = self.dataproc.outCombo.currentIndex()

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
            if type(parameter) == str:
                ds = parameter

            else:
                ds = parameter[j-startplot]

            if not self.qplotss['windows'][j].win.isVisible():
                self.qplotss['windows'][j].__init__(figsize=self.qplotss['positions'][j][0:2],
                                                    fig_x_position=self.qplotss['positions'][j][2],
                                                    fig_y_position=self.qplotss['positions'][j][3], remote=False, window_title=self.dataproc.outCombo.itemText(j))

            self.qplotss['windows'][j].clear()

            nanarray = ~(np.isnan(getattr(self.dataset, ds).set_arrays[0]))
            self.nanvalues = nanarray

            __array = list(getattr(self.dataset, ds).set_arrays)

            if len(__array) == 1:
            # if np.shape(getattr(self.dataset, ds).set_arrays)[0] == 1:

                self.qplotss['windows'][j].add(x=getattr(self.dataset, ds).set_arrays[0][nanarray], y=getattr(self.dataset, ds).ndarray[nanarray],
                                               xlabel=getattr(self.dataset, ds).set_arrays[0].name, ylabel=getattr(self.dataset, ds).name,
                                               xunit=getattr(self.dataset, ds).set_arrays[0].unit, yunit=getattr(self.dataset, ds).unit)

                self.dataproc.freezeCmap.setEnabled(False)
                self.dataproc.getLinecut.setEnabled(False)

            elif len(__array) == 2:
            # elif np.shape(getattr(self.dataset, ds).set_arrays)[0] == 2:
                self.dataproc.freezeCmap.setEnabled(True)
                self.dataproc.getLinecut.setEnabled(True)

                X = []
                Z = []
                Xset_array=np.tile(getattr(self.dataset, ds).set_arrays[1][0],(np.shape(getattr(self.dataset, ds).set_arrays[0])[0],1))
                for Xx, Zz in zip(Xset_array[nanarray], getattr(self.dataset, ds).ndarray[nanarray]):
                # for Xx, Zz in zip(getattr(self.dataset, ds).set_arrays[1][nanarray], getattr(self.dataset, ds).ndarray[nanarray]):
                    sortinds = np.argsort(Xx)[::-1]
                    X.append(Xx[sortinds])
                    Z.append(Zz[sortinds])

                self.Y = getattr(self.dataset, ds).set_arrays[0][nanarray]
                self.X = X
                self.Z = np.flip(np.rot90(Z), 0) # Z

                self.qplotss['windows'][j].add(x=self.Y, y=self.X, z=self.Z,
                                               xlabel=getattr(self.dataset, ds).set_arrays[0].name, ylabel=getattr(
                                                   self.dataset, ds).set_arrays[1].name, zlabel=getattr(self.dataset, ds).name,
                                               xunit=getattr(self.dataset, ds).set_arrays[0].unit, yunit=getattr(self.dataset, ds).set_arrays[1].unit, zunit=getattr(self.dataset, ds).unit)

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

            try:
                self.data_plots[j] = getattr(self.dataset, ds)
            except:
                self.data_plots.append(getattr(self.dataset, ds))

            j += 1

            self.dataproc.getCoord.setChecked(False)
            self.dataproc.getLinecut.setChecked(False)

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

    def toggle_getcoord(self):
        if self.dataproc.getCoord.isChecked():
            if self.dataproc.outCombo.currentText() == 'All':
                for i in range(len(self.qplotss['windows'])):
                    self._enablecoord(i)
            else:
                indp = self.dataproc.outCombo.currentIndex()
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
            # print(evt)
            # print(ind)
            pos = evt  # using signal proxy turns original arguments into a tuple
            vb = self.pplot[ind].vb
            sx, sy = vb.viewPixelSize()
            self.pplot[ind].setCursor(QtCore.Qt.BlankCursor)

            if self.pplot[ind].sceneBoundingRect().contains(pos):
                mousePoint = vb.mapSceneToView(pos)
                index_x = mousePoint.x()
                index_y = mousePoint.y()

                if len(self.data_plots[ind].set_arrays) == 1:
                    # self.label[ind].setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y=%f</span>" % (index_x, index_y))
                    self.label[ind].setText(
                        "x=%0.1f \r y=%f" % (index_x, index_y))
                else:
                    # self.label[ind].setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y=%0.1f</span>,   <span style='color: green'>z=%E</span>" % (index_x, index_y, get_z(index_y,index_x,self.data_plots[ind])))
                    self.label[ind].setText("x=%0.1f \r y=%0.1f \r z=%E" % (
                        index_x, index_y, get_z(index_y, index_x, self.data_plots[ind])))

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
                indx_fine, indy_fine = plot_tools.get_indices(Z, x, y)
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


    def toggle_linecut(self):
        if self.dataproc.getLinecut.isChecked():
            if self.dataproc.outCombo.currentText() == 'All':
                for i in range(len(self.qplotss['windows'])):
                    self._enable_linecut(i)
            else:
                indp = self.dataproc.outCombo.currentIndex()
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
                x, y = get_cut(self.data_plots[ind], self.cutdir, valy, valx)

                if self.plot_linecuts:
                    self.plot_linecuts[0].clear()
                else:
                    self.plot_linecuts.append(pg.GraphicsWindow())
                if self.cutdir == 1:
                    self.plot_linecuts[0].setWindowTitle(
                        'Line cut at x ='+str(valx))
                elif self.cutdir == 0:
                    self.plot_linecuts[0].setWindowTitle(
                        'Line cut at y ='+str(valy))

                p1 = self.plot_linecuts[0].addPlot(row=0, col=0)
                p1.plot(x=x, y=y, pen="r")

        def get_cut(Z, dir_ind, x, y):

            indx_fine, indy_fine = plot_tools.get_indices(Z, x, y)

            nanarray_y = ~(np.isnan(Z.set_arrays[0]))

            y_array = Z.set_arrays[0][nanarray_y]
            y_numel = len(Z.set_arrays[0][nanarray_y])
            y_span = Z.set_arrays[0][y_numel-1]-Z.set_arrays[0][0]

            nanarray_x = ~(np.isnan(Z.set_arrays[1][indy_fine]))

            x_array = Z.set_arrays[1][indy_fine][nanarray_x]
            x_numel = len(Z.set_arrays[1][indy_fine][nanarray_x])
            x_span = Z.set_arrays[1][indy_fine][x_numel-1] - \
                Z.set_arrays[1][indy_fine][0]

            if dir_ind == 0:  # y direction
                x = y_array  # Z.set_arrays[dir_ind-1]
                y = []

                if Z.set_arrays[1][0][0] != Z.set_arrays[1][1][0]:
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
