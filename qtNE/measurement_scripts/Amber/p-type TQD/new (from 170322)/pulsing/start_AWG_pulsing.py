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
    
    twait = 300e-9 #600e-9#*10 for oscilloscope visualization  # first wait time (s)
    tblock= 300e-9#*10 for oscilloscope visualization
    tinter = 300e-9#*10 for oscilloscope visualization # 1e-6  # the second wait time (s) - time between pulses

    # Voltage on each gate 
    # WARNING: the input voltage is twice this value due to high input impedance (very resistive sample)
    #Multiplication factor to correct for attenuation along coaxial lines
    MF_III = 
    MF_IV = 156.25
    
    high_level_RB = 5 * 1e-3 * MF_III # 2000 * 1e-3# 2250 * 1e-3  # the high level (V)
    high_level_LB = -5.2 * 1e-3 * MF_IV #-350 * 1e-3 # 2000 * 1e-3 # the high level (V)


    # --------------------------------- Create the blueprints
    baseshape_empty = bb.BluePrint()
    baseshape_empty.setSR(SR)
    baseshape_empty.insertSegment(0, ramp, (0, 0), dur=twait)
    baseshape_empty.insertSegment(1, ramp, (0,0), dur=tblock)
    baseshape_empty.insertSegment(2, ramp, (0, 0), dur=tinter)
    
    ###### RB - ch4

    baseshape_RB = bb.BluePrint()
    baseshape_RB.setSR(SR)
    baseshape_RB.insertSegment(0, ramp, (0, 0), dur=twait)
    baseshape_RB.insertSegment(1, ramp, (high_level_RB, high_level_RB), dur=tblock)
    baseshape_RB.insertSegment(2, ramp, (0, 0), dur=tinter)
    # baseshape_RB.insertSegment(0, ramp, (-high_level_RB/2, -high_level_RB/2), dur=twait)
    # baseshape_RB.insertSegment(1, ramp, (high_level_RB/2, high_level_RB/2), dur=tblock)
    # baseshape_RB.insertSegment(2, ramp, (-high_level_RB/2, -high_level_RB/2), dur=tinter)

    ###### LB - ch1

    baseshape_LB = bb.BluePrint()
    baseshape_LB.insertSegment(0, ramp, (0, 0), dur=twait)
    baseshape_LB.insertSegment(1, ramp, (high_level_LB, high_level_LB), dur=tblock)
    baseshape_LB.insertSegment(2, ramp, (0, 0), dur=tinter)
    baseshape_LB.setSR(SR)


    ########## pulse modulation - ch3

    # SR = 1.2e9
    high_level_pulse = 0.0  # the high level (V) - for pulse modulation
    # high_level_pulse = 0.5  # the high level (V) - for IQ modulation (I)
    
    tdrive=100e-9
    # tdrive=200e-9#*10 for oscilloscope visualization
    tdelay=85e-9 # delay between TRIG IN and MW burst generation
    ttrans=20e-9


    baseshape_pulse = bb.BluePrint()
    baseshape_pulse.setSR(SR)
    baseshape_pulse.insertSegment(0, ramp, (0, 0), dur=twait+(tblock-tdrive)-tdelay-ttrans)
    baseshape_pulse.insertSegment(1, ramp, (high_level_pulse, high_level_pulse), dur=tdrive)
    baseshape_pulse.insertSegment(2, ramp, (0, 0), dur=tinter+tdelay+ttrans)




    # --------------------------------- Create element

    baseelem = bb.Element()
    baseelem.addBluePrint(1, baseshape_empty)
    baseelem.addBluePrint(2, baseshape_LB)
    baseelem.addBluePrint(3, baseshape_pulse)
    baseelem.addBluePrint(4, baseshape_RB)

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

    A_ch1=4.5
    OFF_ch1=0.0#0 # A_ch1/2
    awg.ch1_amp.set(A_ch1)
    awg.ch1_offset.set(OFF_ch1)

    A_ch2=4.5
    OFF_ch2=0.0# 0#A_ch2/2
    awg.ch2_amp.set(A_ch2)
    awg.ch2_offset.set(OFF_ch2)


    ##### DO NOT CHANGE! output for MW source trigger input
    A_ch3=2.0
    OFF_ch3=0#A_ch3/2
    awg.ch3_amp.set(A_ch3)
    awg.ch3_offset.set(OFF_ch3)
    ######
    
    A_ch4=4.5
    OFF_ch4=0.0#0 # A_ch1/2
    awg.ch4_amp.set(A_ch4)
    awg.ch4_offset.set(OFF_ch4)


    # --------------------------------- Convert and export sequence to AWG

    seq.setChannelAmplitude(1,A_ch1)
    seq.setChannelOffset(1,OFF_ch1)    
    seq.setChannelAmplitude(2,A_ch2)
    seq.setChannelOffset(2,OFF_ch2)
    seq.setChannelAmplitude(3,A_ch3)
    seq.setChannelOffset(3,OFF_ch3)
    seq.setChannelAmplitude(4,A_ch4)
    seq.setChannelOffset(4,OFF_ch4)
    


    awg_input= seq.outputForAWGFile()# seq.outputForAWGFile()

    awg.make_send_and_load_awg_file(*awg_input[:])


    # 

inf_pulse(station.awg)

station.awg.ch4_state(1)
station.awg.ch2_state(1)
#station.awg.ch3_state(1)
station.awg.run()

# drive hole in resonance
# station.psg.frequency.set(1.0e6) #previously set to 16.7e9
# station.psg.power.set(-8)
station.psg.modulation.set('OFF')
station.psg.off()

print('Chs 1 and 2 ON and pulse started')
