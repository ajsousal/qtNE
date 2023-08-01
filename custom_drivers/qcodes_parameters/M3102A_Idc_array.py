import qcodes


## -- instrument definitions

instrument_name = 'digitizer'
target_instrument = station.components[instrument_name]
IV_converter_gain = 1


# -- parameter definitions

parameter_name = 'Idc'


# -- auxiliary functions


# -- parameter creation and add to station


parameter = qcodes.Parameter(
    parameter_name,
    label='SD current',
    unit='A',
    instrument=target_instrument,
    get_cmd=lambda : target_instrument.reader.array_daq_1
)

station.add_component(parameter)
