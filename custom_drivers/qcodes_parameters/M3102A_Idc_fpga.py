import qcodes


## -- instrument definitions

instrument_name = 'digi'
target_instrument = station.components[instrument_name]
IV_converter_gain = 1


# -- parameter definitions

parameter_name = 'Idc'


# -- auxiliary functions

def get_reading_fpga(channel,reg_bank,reg):
    target_instrument.trigger(channel)
    value = target_instrument.fpga_read_registerbank(reg_bank,reg)
    value = value*station[instrument_name].fullscale/2**station[instrument_name].bit_depth/IV_converter_gain

    return value


# -- parameter creation and add to station


parameter = qcodes.Parameter(
    parameter_name,
    label='SD current',
    unit='A',
    instrument=target_instrument,
    get_cmd=lambda ch = channel, rdatabank=self.databank, regdata=self.regdata: get_reading_fpga(ch,rdatabank,regdata)
)

station.add_component(parameter)
