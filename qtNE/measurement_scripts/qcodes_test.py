import os
import time

import numpy as np

import qcodes.logger
from qcodes.dataset import (
    Measurement,
    initialise_or_create_database_at,
    load_or_create_experiment,
    do1d
)
from qcodes.tests.instrument_mocks import (
    DummyInstrument,
    DummyInstrumentWithMeasurement,
)
from qcodes.utils.dataset.doNd import plot

initialise_or_create_database_at('C:\qtNE_dbs_2021\db_test.db')

dac = DummyInstrument("dac", gates=["ch1", "ch2"])
dmm = DummyInstrumentWithMeasurement("dmm", setter_instr=dac)

tutorial_exp = load_or_create_experiment("doNd_VS_Measurement", sample_name="no sample")

do1d(dac.ch1, 0, 1, 10, 0.01, dmm.v1, dmm.v2, show_progress=True)

