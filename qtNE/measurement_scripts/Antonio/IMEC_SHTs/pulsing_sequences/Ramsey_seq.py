import broadbean as bb
from broadbean import ripasso as rp
from broadbean.plotting import plotter
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.figsize'] = (8, 3)
mpl.rcParams['figure.subplot.bottom'] = 0.15 

# from qcodes.instrument_drivers.tektronix.AWGFileParser import parse_awg_file  # <--- A helper function

import matplotlib.pyplot as plt
import numpy as np
import os
from decimal import *


# import qcodes.instrument_drivers.tektronix.AWG5014 as AWG5014
# awg=AWG5014.Tektronix_AWG5014(name='awg',address='GPIB0::1::INSTR')

# using broadbeans
def sequence(instrument,tseparation,**kwargs):

    # print(tburst)
    print(tseparation)
    print('Pulsing RB and E8257D, Ramsey')

    awg=instrument
    
    ramp=bb.PulseAtoms.ramp

    ##### settings


    SR = 1.0e9
    awg.clock_freq.set(SR)
    
    twait = 600e-9 #600e-9#*10 for oscilloscope visualization  # first wait time (s)
    tblock= 400e-9#*10 for oscilloscope visualization
    tinter = 600e-9#*10 for oscilloscope visualization # 1e-6  # the second wait time (s) - time between pulses

    
    # Voltage on each gate 
    # WARNING: the input voltage is twice this value due to high input impedance (very resistive sample)
    high_level_RB = -500 * 1e-3 #0 * 1e-3# 2250 * 1e-3  # the high level (V)
    high_level_LB = 0 * 1e-3#-350 * 1e-3 # the high level (V)


    # --------------------------------- Create the blueprints
    ###### RB - ch2

    baseshape_RB = bb.BluePrint()
    baseshape_RB.setSR(SR)
    # baseshape_RB.insertSegment(0, ramp, (0, 0), dur=twait)
    # baseshape_RB.insertSegment(1, ramp, (high_level_RB, high_level_RB), dur=tblock)
    # baseshape_RB.insertSegment(2, ramp, (0, 0), dur=tinter)
    baseshape_RB.insertSegment(0, ramp, (-high_level_RB/2, -high_level_RB/2), dur=twait)
    baseshape_RB.insertSegment(1, ramp, (high_level_RB/2, high_level_RB/2), dur=tblock)
    baseshape_RB.insertSegment(2, ramp, (-high_level_RB/2, -high_level_RB/2), dur=tinter)
    
    # plotter(baseshape_RB)

    ###### LB - ch1

    baseshape_LB = bb.BluePrint()
    baseshape_LB.setSR(SR)
    baseshape_LB.insertSegment(0, ramp, (0, 0), dur=twait)
    baseshape_LB.insertSegment(1, ramp, (high_level_LB, high_level_LB), dur=tblock)
    baseshape_LB.insertSegment(2, ramp, (0, 0), dur=tinter)
    


    ########## pulse modulation - ch3

    # SR = 1.2e9
    high_level_pulse = 1.0  # the high level (V)
    # high_level_pulse = 0.5  # the high level (V) - for IQ modulation (I)
    # tdrive=tburst
    tdrive=10e-9
    ttrans=30e-9#1e-9
    tdelay=85e-9
    tsep=np.round(tseparation,9)
    # tdrive=200e-9#*10 for oscilloscope visualization
    tsep2_left=np.round(np.floor(tsep*1e9/2)*1e-9,9)
    tsep2_right=np.round(np.ceil(tsep*1e9/2)*1e-9,9)

    # print(np.floor(tblock/1e-9/2)*1e-9)
    # print(np.floor(tsep/1e-9/2)*1e-9)
    print(tsep)
    print(tsep2_right)
    print(tsep2_left)
    
    if tsep2_left+tsep2_right!=tsep:
        tsep2_left+=(tsep-(tsep2_left+tsep2_right))
        
    print(tsep2_left)

    baseshape_pulse = bb.BluePrint()
    baseshape_pulse.setSR(SR)
    # in middle of manip pulse
    baseshape_pulse.insertSegment(0, ramp, (0, 0), dur=twait+np.round(tblock/2,9)-tsep2_left-tdelay-tdrive)
    baseshape_pulse.insertSegment(1, ramp, (high_level_pulse, high_level_pulse), dur=tdrive)
    baseshape_pulse.insertSegment(2, ramp, (0, 0), dur=tsep)
    baseshape_pulse.insertSegment(3, ramp, (high_level_pulse, high_level_pulse), dur=tdrive)
    baseshape_pulse.insertSegment(4, ramp, (0, 0), dur=np.round(tblock/2,9)-tsep2_right+tinter-tdrive+tdelay)
    
    # at end of manip pulse
    # baseshape_pulse.insertSegment(0, ramp, (0, 0), dur=twait+tblock-tdrive-tsep-tdrive-ttrans-tdelay)
    # baseshape_pulse.insertSegment(1, ramp, (high_level_pulse, high_level_pulse), dur=tdrive)
    # baseshape_pulse.insertSegment(2, ramp, (0, 0), dur=tsep)
    # baseshape_pulse.insertSegment(3, ramp, (high_level_pulse, high_level_pulse), dur=tdrive)
    # baseshape_pulse.insertSegment(4, ramp, (0, 0), dur=ttrans+tdelay+tinter)#tblock/2-tsep/2+tinter-tdrive+tdelay)
    

    # --------------------------------- Create element

    baseelem = bb.Element()
    baseelem.addBluePrint(1, baseshape_LB)
    baseelem.addBluePrint(2, baseshape_RB)
    baseelem.addBluePrint(3, baseshape_pulse)


    # --------------------------------- Create sequence

    nruns=0#1e6

    seq = bb.Sequence()
    seq.setSR(SR)
    elem = baseelem.copy()
    seq.addElement(1, elem)
    seq.setSequencingNumberOfRepetitions(1,nruns)
    seq.setSequencingTriggerWait(1,0)
    seq.setSequencingEventJumpTarget(1,0)
    seq.setSequencingGoto(1,1)

    seq.name = 'test_sequence'  # the sequence name will be needed later


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


    # --------------------------------- Convert and export sequence to AWG

    seq.setChannelAmplitude(1,A_ch1)
    seq.setChannelOffset(1,OFF_ch1)
    seq.setChannelAmplitude(2,A_ch2)
    seq.setChannelOffset(2,OFF_ch2)
    seq.setChannelAmplitude(3,A_ch3)
    seq.setChannelOffset(3,OFF_ch3)


    awg_input= seq.outputForAWGFile()# seq.outputForAWGFile()

    awg.make_send_and_load_awg_file(*awg_input[:])


    # print('changed now')
    tsequence=nruns*(twait+tblock+tinter)
    tavg=twait+tinter
    tmanip=tblock
    
    # awg.ch1_state.set(1)
    awg.ch2_state.set(1)
    awg.ch3_state.set(1)
    
    return tavg, tmanip
