# %% Load packages

## test push

import argparse
import logging
import os

import pyqtgraph as pg
# import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
# from qtpy.QtWidgets import QFileDialog, QWidget

import qcodes

from .instruments.ivviGUI import IVVIGUI
from .instruments.Agilent33250GUI import Agilent33250GUI
from .instruments.MercuryiPSGUI import MercuryiPSGUI

import json
import pickle
from tempfile import gettempdir

from stat import S_IREAD, S_IRWXU


from source.tools import json_interpreter as json_handling_db # change this import in the future

from source.tools import tmp_tools as tmp_tools # change this import in the future

from source.gui.dataviewer import (
            dataviewer,
            dataviewer_new,
            dataviewmeta,
            dataviewprocess)

from source.gui.measuregui import measqueuer

from source.tools.safe_thread import Thread

from source.gui.new_measgui import meas_creator

from source.gui.instruments import stationOverview


class StationGUI(QtWidgets.QMainWindow):

    def __init__(self,station=None,database_dir=None):
        """ 
        """
        super(StationGUI, self).__init__()


        self.station = station

        self.database_dir = database_dir

        with open('qtNE.cfg','r') as cfg:
            self.config_json=json.load(cfg)

        tmp_tools.set_status(1)

        self.meas_running=False


## ------------- horizontal layouts

        userLayout = QtWidgets.QHBoxLayout()

        self.userText = QtWidgets.QLabel()
        self.userText.setText('User:')
        self.userCombo = QtWidgets.QComboBox()
        self.setUser = QtWidgets.QPushButton()
        self.setUser.setText('Set User')

        instrumentLayout = QtWidgets.QHBoxLayout()

        self.InstrText = QtWidgets.QLabel()
        self.InstrText.setText('Instrument:')
        self.InstrStartButton = QtWidgets.QPushButton()
        self.InstrStartButton.setText('Front Panel')
        self.InstrSelect = QtWidgets.QComboBox()


        self.DataView = QtWidgets.QPushButton()
        self.DataView.setText('Data Viewer')

        userLayout.addWidget(self.userText)
        userLayout.addWidget(self.userCombo)
        userLayout.addWidget(self.setUser)

        instrumentLayout.addWidget(self.InstrText)
        instrumentLayout.addWidget(self.InstrSelect)
        instrumentLayout.addWidget(self.InstrStartButton)

        self.MeasQueuer = QtWidgets.QPushButton()
        self.MeasQueuer.setText('Measurement Queuer')

        self.JupyterCall = QtWidgets.QPushButton()
        self.JupyterCall.setText('Open Jupyter Notebooks')

        self.StationOverview = QtWidgets.QPushButton()
        self.StationOverview.setText('Station Setup')

        # self.MeasCreator = QtWidgets.QPushButton()
        # self.MeasCreator.setText('Measurement Creator')

## ------------- vertical layout

        vertLayout = QtWidgets.QVBoxLayout()

        vertLayout.addItem(userLayout)
        vertLayout.addItem(instrumentLayout)
        vertLayout.addWidget(self.DataView)
        vertLayout.addWidget(self.MeasQueuer)
        # vertLayout.addWidget(self.MeasCreator)
        vertLayout.addWidget(self.JupyterCall)
        vertLayout.addWidget(self.StationOverview)

        

        widget = QtWidgets.QWidget()
        widget.setLayout(vertLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Station GUI')
        self.setGeometry(1000, 30, 300, 100)


        self.show()



## ------------- Populate comboboxes and buttons

        self.instr_names = self.populate_instr(self.station)
        for kk in self.instr_names:
            self.InstrSelect.addItem(kk)

        self.user_names = self.populate_users(self.database_dir)
        for kk in self.user_names:
            self.userCombo.addItem(kk)

 

## ------------- Buttons actions

        self.InstrStartButton.clicked.connect(self.InstrStart_callback)
        self.userCombo.activated.connect(self.enable_user)
        self.setUser.clicked.connect(self.setUser_callback)
        self.DataView.clicked.connect(self.dataView_callback)

        self.MeasQueuer.clicked.connect(self.measqueuer_callback)
        
        # self.MeasCreator.clicked.connect(self.meascreator_callback)
        self.JupyterCall.clicked.connect(self.jupytercall_callback)
        self.StationOverview.clicked.connect(self.stationoverview_callback)


## ------------- Initialize to default user


        self.set_user_directories(self.userCombo.currentText())

        # self.native_parameters_dict = self.return_parameter_list() # dictionary containing native parameters for every station component VIP: to be used also for autoGUI



## -------------- Retrieve parameters from station components
    
    # def return_parameter_list(self):
    #     parameters_dictionary = {}
    #     for component in self.station.components:
    #         parameters_dictionary[component] = list(self.station.components[component].parameters)

    #     return parameters_dictionary

    
## -------------  GUI functions


    def enable_user(self):
        self.setUser.setEnabled(True)


    def populate_users(self,database_dir):
        list_users = []

        try:

            for directory in os.listdir(database_dir):
                if os.path.isdir(os.path.join(database_dir,directory)):
                    list_users.append(directory)

            return list_users

        except:

            print('Error loading database directory.')
            return



    def populate_instr(self,station):
        list_instr_names = []

        try:
            for aa in station.components:
                if str(type(station.components[aa])).find('Virtual')==-1:
                    try:
                        list_instr_names.append(station.components[aa].name)    
                    except:
                        list_instr_names.append(aa)
                        

            return list_instr_names

        except:
            print('Station is not defined.')
            return


    def InstrStart_callback(self):

        """
        Call for instruments GUIs.
        """

        self.actInstr = self.InstrSelect.currentText()

        if str(type(self.station.components[self.actInstr])).find('IVVI')!=-1:                    
            self.ivviGUI=IVVIGUI(self)
            self.ivviGUI.show()

        elif str(type(self.station.components[self.actInstr])).find('WaveformGenerator_33XXX')!=-1:                    
            print(self.actInstr)
            self.Agilent33250GUI=Agilent33250GUI(self.actInstr,self)
            self.Agilent33250GUI.show()

        elif str(type(self.station.components[self.actInstr])).find('MercuryiPS')!=-1:                    
            print(self.actInstr)
            self.MercuryiPSGUI=MercuryiPSGUI(self)
            self.MercuryiPSGUI.show()

        # elif str(type(self.station.components[self.actInstr])).find('Keithley_2000'):
                    # self.keithGUI=KeithGUI(self)
                    # self.keithGUIGUI.show()
        else: 
            print('GUI for this instrument is not available')


    def set_user_directories(self,username=None):


        self.parent_meas= self.config_json['measurementdir']
        self.parent_db=self.config_json['datadir']

        self.current_directories= {'current_db': os.path.join(self.parent_db,username),
                                   'current_meas': os.path.join(self.parent_meas,username)
                                    }
        with open(os.path.join(gettempdir(),'tmp'),"ab") as f:
            pickle.dump(self.current_directories,f)



    def setUser_callback(self):

        """
        Set measurement database at current user folder
        """

        self.set_user_directories(self.userCombo.currentText())
        self.setUser.setEnabled(False)



    def dataView_callback(self):

        """
        Call for DataViewer at current user data folder
        """

        tempdata=tmp_tools.read_tmp(tmp_file='tmp')

        datadir=tempdata['current_db']

        # self.dataviewer=dataviewer.DataViewer(data_directory = datadir)
        self.dataviewer=dataviewer_new.DataViewer(data_directory = datadir)



    def measqueuer_callback(self):

        tempdata=tmp_tools.read_tmp(tmp_file='tmp')
        tempdir=tempdata['temp_dir']

        self.measqueuer=measqueuer.MeasQueuer(self,temp_dir=tempdir)
        self.measqueuer.show()


    def meascreator_callback(self):

        # tempdata=tmp_tools.read_tmp(tmp_file='tmp')
        # tempdir=tempdata['temp_dir']

        self.meascreator=meas_creator.MeasurementCreator(self)
        self.meascreator.show()


    def stationoverview_callback(self):
        self.stationoverview=stationOverview.stationOverview(self)
        self.stationoverview.show()

    def jupytercall_callback(self):

        import subprocess

        nb_dir=self.current_directories['current_db']+'\jupyter_nbs'

        filepath="run_jupyter.bat"
        p = subprocess.Popen([filepath, nb_dir], shell=True)#, stdout = subprocess.PIPE)

        # import errno
        # import select
        # from threading import Thread

        # def non_blocking_communicate(proc, inputs):
        #     """non blocking version of subprocess.Popen.communicate.
        #     `inputs` should be a sequence of bytes (e.g. file-like object, generator,
        #     io.BytesIO, etc.).
        #     """

        #     def write_proc(proc, inputs):
        #         for line in inputs:
        #             try:
        #                 proc.stdin.write(line)
        #             except IOError as e:
        #                 # break at "Broken pipe" error, or "Invalid argument" error.
        #                 if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
        #                     break
        #                 else:
        #                     raise
        #         proc.stdin.close()

        #     t = Thread(target=write_proc, args=(proc, inputs))
        #     t.start()

        #     while proc.poll() is None:
        #         if select.select([proc.stdout], [], [])[0]:
        #             line = proc.stdout.readline()
        #             if not line:
        #                 break
        #             yield line

        #     proc.wait()
        #     t.join()

        # stdout, stderr = non_blocking_communicate(p)

        return

    def runmeas_callback(self):

        """
        Run experiment json
        """

        if self.measqueuer.queue.model().rowCount()>0:

            self.fname=self.measqueuer.queue.model().item(0).text()

            self.t = Thread(target = self.exp_run)
            self.t.start()
            # self.t.isAlive()
            self.t.is_alive() # change in Python 3.9

            self.meas_running=True

            self.measqueuer.StopMeasurement.setEnabled(True)
            self.measqueuer.RunMeasurement.setEnabled(False)

        else: 
            print('Measurement queue is empty.')
            self.meas_running=False
            self.measqueuer.StopMeasurement.setEnabled(False)



    def cleanqueue(self,file,itemindex):

        """
        Clear finised run and calls for next run in the queue (recursively)
        """  

        os.chmod(file, S_IRWXU)
        os.remove(file)
        self.measqueuer._queue.removeRow(self.measqueuer.queue.model().item(itemindex).row())
        
        try:
            fname=self.measqueuer.queue.model().item(0).text()
        except:
            fname=[]

        self.runmeas_callback()



    def stopmeas_callback(self):
        self.t.terminate()
        self.t.join()

        self.meas_running=False

        self.stopbutton_disable()
        print("Measurement stopped by user.")




    def stopbutton_disable(self):    
        # self.StopMeasurement.setEnabled(False)
        self.measqueuer.StopMeasurement.setEnabled(False)
        self.measqueuer.RunMeasurement.setEnabled(True)



    def closeEvent(self, event):
        print("closing StationGUI")
        self.station.close_all_registered_instruments()

        self.meas_running=False

        os.remove(os.path.join(gettempdir(),'tmp'))

        tmp_tools.set_status(0)




    def exp_run(self):

        if self.fname:
            if self.fname.endswith('.json'):
                self.runmeas = json_handling_db.jsonExperiment(self.station,self.fname)
                self.runmeas.run_experiment()
            elif self.fname.endswith('.py'):
                try:
                    exec(open(self.fname).read(),{'station': self.station})
                    # os.system('python '+self.fname)
                except SystemExit:
                    print('Error loading script.')
            else:
                print('Not a valid experiment file')

            self.cleanqueue(self.fname,0)
            # self.stopbutton_disable()

        else:
            print('Queue is empty.')
            return





if __name__ == '__main__':
    import sys

    stdout = sys.stdout
    reload(sys)
    sys.setdefaultencoding('utf-8')
    sys.stdout = stdout
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
    # app = QApplication([])

    # StationGUI = StationGUI()
    # # StationGUI.show()
    # app = pg.mkQApp()

    # StationGUI = StationGUI()
    # StationGUI.show()

    # from PyQt5.QtWidgets import QApplication
    # app = QApplication(sys.argv)
    StationGUI = StationGUI()
    # StationGUI.show()
    # app.exec_()
