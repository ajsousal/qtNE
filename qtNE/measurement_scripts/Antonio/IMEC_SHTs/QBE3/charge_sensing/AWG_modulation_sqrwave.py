import broadbean as bb
from broadbean import ripasso as rp
from broadbean.plotting import plotter
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.figsize'] = (8, 3)
mpl.rcParams['figure.subplot.bottom'] = 0.15 


import matplotlib.pyplot as plt
import numpy as np
import os

def inf_pulse(instrument):

    awg=instrument

    # using broadbeans

    ramp=bb.PulseAtoms.ramp

    ##### settings


    SR = 1.0e9
    awg.clock_freq.set(SR)


    freq_mod=532 #Hz
    amp_mod=0.015 #V

    baseshape_modulation = bb.BluePrint()
    baseshape_modulation.setSR(SR)
    baseshape_modulation.insertSegment(0,ramp, (-amp_mod,-amp_mod),dur=1/freq_mod/2)
    baseshape_modulation.insertSegment(1,ramp,(amp_mod,amp_mod),dur=1/freq_mod/2)

    high_level_pulse = 0.2  # the high level (V) - for pulse modulation

    baseshape_trigger = bb.BluePrint()
    baseshape_trigger.setSR(SR)
    baseshape_trigger.insertSegment(0, ramp, (0, 0), dur=1/freq_mod/2)
    baseshape_trigger.insertSegment(1, ramp, (high_level_pulse, high_level_pulse), dur=1/freq_mod/2)

    # --------------------------------- Create element

    baseelem = bb.Element()
    baseelem.addBluePrint(1, baseshape_trigger)
    baseelem.addBluePrint(2, baseshape_modulation)


    # --------------------------------- Create sequence

    seq = bb.Sequence()
    seq.setSR(SR)
    elem = baseelem.copy()
    seq.addElement(1, elem)
    seq.setSequencingNumberOfRepetitions(1,0)

    seq.name = 'test_sequence'  # the sequence name will be needed later

    # plotter(seq)
    
    print(seq.checkConsistency())  # returns True if all is well, raises errors if not


    # --------------------------------- Voltage settings in AWG - remember 50Ohm output!

    # awg.clock_freq.get()

    # A_ch1=4.5
    # OFF_ch1=0.0#0 # A_ch1/2
    # awg.ch1_amp.set(A_ch1)
    # awg.ch1_offset.set(OFF_ch1)

    # A_ch2=4.5
    # OFF_ch2=0.0# 0#A_ch2/2
    # awg.ch2_amp.set(A_ch2)
    # awg.ch2_offset.set(OFF_ch2)


    ##### DO NOT CHANGE! output for MW source trigger input
    A_ch1=2.0
    OFF_ch1=0#A_ch3/2
    awg.ch1_amp.set(A_ch1)
    awg.ch1_offset.set(OFF_ch1)
    ######

    ##### DO NOT CHANGE! output for MW source trigger input
    A_ch2=2.0
    OFF_ch2=0#A_ch3/2
    awg.ch2_amp.set(A_ch2)
    awg.ch2_offset.set(OFF_ch2)
    ######


    # --------------------------------- Convert and export sequence to AWG

    seq.setChannelAmplitude(1,A_ch1)
    seq.setChannelOffset(1,OFF_ch1)
    seq.setChannelAmplitude(2,A_ch2)
    seq.setChannelOffset(2,OFF_ch2)
    # seq.setChannelAmplitude(3,A_ch3)
    # seq.setChannelOffset(3,OFF_ch3)
    # seq.setChannelAmplitude(4,A_ch4)
    # seq.setChannelOffset(4,OFF_ch4)


    awg_input= seq.outputForAWGFile()# seq.outputForAWGFile()

    awg.make_send_and_load_awg_file(*awg_input[:])


    # 

inf_pulse(station.awg)

# station.awg.ch1_state(1)
# station.awg.ch2_state(1)
# station.awg.ch3_state(1)
station.awg.ch1_state(1)
station.awg.ch2_state(1)
station.awg.run()

# drive hole in resonance
# station.psg.frequency.set(16.7e9)
# station.psg.power.set(-6)
# station.psg.modulation.set('ON')
# station.psg.on()

print('Chs 4 ON and pulse started')
