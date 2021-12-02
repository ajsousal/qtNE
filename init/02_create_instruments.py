#----------------------%% Instruments initializations

import qcodes.instrument_drivers.tektronix.Keithley_2000 as Keithley2000
from qcodes_contrib_drivers.drivers.QuTech.IVVI import IVVI
import qcodes.instrument_drivers.stanford_research.SR830 as SR830
import qcodes.instrument_drivers.tektronix.AWG5014 as AWG5014
import custom_drivers.KeysightAgilent_33XXX as Agilent33250
from custom_drivers.MercuryiPS_VISA import MercuryiPS
from custom_drivers.AgilentE8257D import Agilent_E8257D
from custom_drivers.Keysight_M3102A import Keysight_M3102A 

#%%Initialize station object
station = qcodes.Station()

#%%Load drivers and add the instruments to the station

ivvi = IVVI(name='ivvi', dac_step=10, dac_delay=0, address='COM5', numdacs=16, polarity = ['BIP', 'BIP', 'BIP', 'NEG'], use_locks=False)
station.add_component(ivvi)

inter_delay = 10e-3
step = 1 # mV

for i in range(16):
	setattr(getattr(station.ivvi,'dac'+str(i+1)),'inter_delay',inter_delay)
	setattr(getattr(station.ivvi,'dac'+str(i+1)),'step',step)


keithley1 = Keithley2000.Keithley_2000(name='keith1', address='GPIB0::17::INSTR')
station.add_component(keithley1)


keithley2 = Keithley2000.Keithley_2000(name='keith2', address='GPIB0::15::INSTR')
station.add_component(keithley2)

# magnet= MercuryiPS(name='magnet',address='COM4')
# station.add_component(magnet)

# psg=Agilent_E8257D(name='psg',address='GPIB0::19::INSTR')
# station.add_component(psg)

# awg=AWG5014.Tektronix_AWG5014(name='awg',address='GPIB0::1::INSTR')
# station.add_component(awg)


# digitizer=Keysight_M3102A(name='digitizer',chassis=1,slot=5)
# station.add_component(digitizer)




# from qcodes.instrument_drivers.Keysight.Keysight_E8267D import Keysight_E8267D
# psg67 = Keysight_E8267D(name='psg67', address='GPIB0::9::INSTR')
# station.add_component(psg67)





# lock_sensor= SR830.SR830(name='lock_sensor',address='GPIB0::9::INSTR')
# station.add_component(lock_sensor)

lock_pulse=  SR830.SR830(name='lock_pulse',address='GPIB0::8::INSTR')
station.add_component(lock_pulse)

wf_pulse=  Agilent33250.WaveformGenerator_33XXX(name='wf_pulse',address='GPIB0::10::INSTR')
station.add_component(wf_pulse)



