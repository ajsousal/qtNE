import numpy as np
from qcodes import ManualParameter, Parameter, validators, Instrument
from quantify.measurement import MeasurementControl
from quantify.measurement import Gettable
import quantify.data.handling as dh
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
from os.path import join
from quantify.data.handling import set_datadir

set_datadir(join(Path.home(), 'quantify-data'))
MC = MeasurementControl("MC")



time = ManualParameter(name='time', label='Time', unit='s', vals=validators.Arrays(), initial_value=np.array([1, 2, 3]))
signal = Parameter(name='sig_a', label='Signal', unit='V', get_cmd=lambda: np.cos(time()))

time.batched = True
time.batch_size = 5
signal.batched = True
signal.batch_size = 10

MC.settables(time)
MC.gettables(signal)
MC.setpoints(np.linspace(0, 7, 23))
dset = MC.run("my experiment")
dset_grid = dh.to_gridded_dataset(dset)

dset_grid.y0.plot()