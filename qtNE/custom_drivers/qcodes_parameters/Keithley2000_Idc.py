import qcodes


## ------------------     Add parameter to retrieve reading from Keithley 2000

instrument_name = 'keith1'
IV_converter_gain = 1


def get_reading():
    station[instrument_name].trigger()
    reading = self.station[instrument_name]._read_next_value()/IV_converter_gain

    return reading


parameter= qcodes.Parameter(
    name = 'Idc',
    instrument = station.components[instrument_name],
    label = 'SD current',
    unit = 'A',
    get_cmd = lambda: get_reading()
)


station.add_component(parameter)


