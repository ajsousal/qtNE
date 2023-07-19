# import sys


import h5py
# import netCDF4
print('passed')

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

from source.gui import stationGUI
            
# from source.measurements.data_set_tools import correctarrays

## -----------------------------------


config_json=json.load(open('qtNE.cfg','r'))

base_dbs = config_json['datadir']
base_meas = config_json['measurementdir']
temp_dir = config_json['tempdir']


directories={"base_dbs": base_dbs, "base_meas": base_meas, "temp_dir": temp_dir}


tempfile.tempdir = temp_dir
tmpname = 'tmp'

if 'external_modules' in config_json:
    if isinstance(config_json['external_modules'],list):
        for module_path in config_json['external_modules']:
            try:
                sys.path.append(module_path)
            except:
                print('Module '+str(module_path)+' not found.')
    else:
        try:
            sys.path.append(config_json['external_modules'])
        except:
            print('Module '+str(module_path)+' not found.')
                


status=tmp_tools.get_status()
if not status is None:
    print('qtNE instance already started!')
    sys.exit()


with open(os.path.join(tempfile.gettempdir(),tmpname), 'wb') as f:
    pickle.dump(directories,f)