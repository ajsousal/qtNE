# import sys

import qcodes

import numpy as np

import types
import os
import time
from time import sleep

from shutil import copy2

import json
import pickle
import tempfile

import source.tools.tmp_tools as tmp_tools

from source.gui.dataviewer import dataviewer
from source.tools import tmp_tools as tmp_tools # change this import in the future

from qtpy.QtWidgets import QApplication
import sys


# from source.measurements.data_set_tools import correctarrays

## -----------------------------------

try:

    config_json=json.load(open('qtNE.cfg','r'))

    base_dbs = config_json['datadir']
    base_meas = config_json['measurementdir']
    temp_dir = config_json['tempdir']

    username=config_json['default_user']


    directories={"base_dbs": base_dbs, "base_meas": base_meas, "temp_dir": temp_dir}


    tempfile.tempdir = temp_dir
    tmpname = 'tmp'


    status=tmp_tools.get_status()
    if not status is None:
        print('qtNE instance already started!')
        sys.exit()


    with open(os.path.join(tempfile.gettempdir(),tmpname), 'wb') as f:
        pickle.dump(directories,f)
        
        
    current_directories={'current_db': os.path.join(base_dbs,username)
                                }
    with open(os.path.join(tempfile.gettempdir(),'tmp'),"ab") as f:
        pickle.dump(current_directories,f) 

    with open(os.path.join(os.getcwd(),'qtNE.cfg'),'r') as cfg_file:
            cfgs=json.load(cfg_file)
            
    tempdata=tmp_tools.read_tmp(tmp_file='tmp')
    print(tempdata)

    datadir=tempdata['current_db']

except:
    print('qtNE_config file not present. Overriding default directories configurations. \n')
    datadir=input('Enter data folder location: ')
    

app=QApplication(sys.argv)

dataviewer=dataviewer.DataViewer(data_directory = datadir)


# stationgui=stationGUI.StationGUI(station=None,database_dir=cfgs['datadir']).dataView_callback()



# import os
# import sys




# if __name__ == '__main__':

    # print('\n \n')
    # print('Starting qtNE dataviewer...\n')

    # basedir= os.getcwd()

    # sys.path.append(os.path.abspath(os.path.join(basedir, 'source')))
    
    
    # filename = os.path.join(basedir, 'source','gui','dataviewer','dataviewer.py')
    # print('Executing %s...' % (filename))
    # try:
        # exec(open(filename).read())
    # except SystemExit:
        # print('')

    # try:
        # del filelist, dir, name, filename
    # except:
        # pass