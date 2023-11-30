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

def inf_pulse(instrument)

    awg=instrument

    # using broadbeans

    ramp=bb.PulseAtoms.ramp

    ##### settings


    SR = 1.2e9
    twait = 600e-9#*10 for oscilloscope visualization  # first wait time (s)
    tblock=400e-9#*10 for oscilloscope visualization
    tinter = 10e-9#*10 for oscilloscope visualization # 1e-6  # the second wait time (s) - time between pulses

    # Voltage on each gate 
    # WARNING: the input voltage is twice this value due to high input impedance (very resistive sample)
    high_level_RB = 0 * 1e-3  # the high level (V)
    high_level_LB = -2250 * 1e-3 # the high level (V)


    # --------------------------------- Create the blueprints
    ###### RB - ch2

    baseshape_RB = bb.BluePrint()
    baseshape_RB.insertSegment(0, ramp, (0, 0), dur=twait)
    baseshape_RB.insertSegment(1, ramp, (high_level_RB, high_level_RB), dur=tblock+tinter)
    baseshape_RB.setSR(SR)
    # plotter(baseshape_RB)

    ###### LB - ch1

    baseshape_LB = bb.BluePrint()
    baseshape_LB.insertSegment(0, ramp, (0, 0), dur=twait)
    baseshape_LB.insertSegment(1, ramp, (high_level_LB, high_level_LB), dur=tblock+tinter)
    baseshape_LB.setSR(SR)


    ########## pulse modulation - ch3

    SR = 1.2e9
    tpredrive=200e-9#*10 for oscilloscope visualization
    high_level_pulse = 1.0  # the high level (V)
    tdrive=200e-9#*10 for oscilloscope visualization



    baseshape_pulse = bb.BluePrint()
    baseshape_pulse.insertSegment(0, ramp, (0, 0), dur=twait+tpredrive)
    baseshape_pulse.insertSegment(1, ramp, (high_level_pulse, high_level_pulse), dur=tdrive)
    baseshape_pulse.insertSegment(2, ramp, (0, 0), dur=(tblock+tinter-tpredrive-tdrive))
    baseshape_pulse.setSR(SR)


    # --------------------------------- Create element

    baseelem = bb.Element()
    baseelem.addBluePrint(1, baseshape_LB)
    baseelem.addBluePrint(2, baseshape_RB)
    baseelem.addBluePrint(3, baseshape_pulse)


    # --------------------------------- Create sequence

    seq = bb.Sequence()
    seq.setSR(SR)
    elem = baseelem.copy()
    seq.addElement(1, elem)
    seq.setSequencingNumberOfRepetitions(1,0)

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




instrument=station.awg
inf_pulse(instrument)


station.awg.ch1_state(1)
station.awg.ch2_state(1)


    # --------------------------------- Enabling AWG

    # awg.ch1_state.set(1)
    # awg.ch2_state.set(1)
    # awg.ch3_state.set(1)

    # awg.run()



    # --------------------------------- Unused stuff

    # awg.ch1_state.set(0)
    # awg.ch2_state.set(0)
    # awg.stop()
    # awg.close()

    # unused commands

    # seq.setSequencingTriggerWait(1, 1)  # 1: trigA, 2: trigB, 3: EXT
    # seq.setSequencingGoto(1, 1)

    # awg_output=awg.make_awg_file(*awg_input[0])
    # awg.send_awg_file('test_square_wf.awg',awg_output)
    # awg.load_awg_file('test_square_wf.awg')
