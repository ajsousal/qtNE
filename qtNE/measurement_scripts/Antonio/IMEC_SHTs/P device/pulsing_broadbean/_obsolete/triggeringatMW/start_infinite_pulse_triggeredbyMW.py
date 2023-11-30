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

def inf_pulse(instrument,t_cb,t_sb):

    awg=instrument
    

    ##### settings


    SR = 1.2e9

    _t_trig_delay=395e-9
    wf_duration=t_cb+t_sb-_t_trig_delay
    
    # Voltage on each gate 
    # WARNING: the input voltage is twice this value due to high input impedance (very resistive sample)
    high_level_RB = 350 * 1e-3 # percentage
    high_level_LB = 350 * 1e-3 # percentage


    # --------------------------------- Create the blueprints
    ###### RB - ch2

    wf_RB=np.zeros(int(wf_duration*SR))
    wf_RB[0:int((t_cb)*SR)]=high_level_RB
    m1_RB=np.zeros(int(wf_duration*SR))
    m2_RB=m1_RB
    
    wf_LB=np.zeros(int(wf_duration*SR))
    wf_LB[0:int((t_cb)*SR)]=high_level_LB
    m1_LB=m1_RB
    m2_LB=m1_LB
    
    # --------------------------------- Voltage settings in AWG - remember 50Ohm output!

    # awg.clock_freq.get()

    A_ch1=2.0
    OFF_ch1=0.0#0 # A_ch1/2
    awg.ch1_amp.set(A_ch1)
    awg.ch1_offset.set(OFF_ch1)

    A_ch2=2.0
    OFF_ch2=0.0# 0#A_ch2/2
    awg.ch2_amp.set(A_ch2)
    awg.ch2_offset.set(OFF_ch2)

    awg.send_waveform_to_list(wf_RB,m1_RB,m2_RB,'wf_RB')
    awg.send_waveform_to_list(wf_LB,m1_LB,m2_LB,'wf_LB')

    awg.ch1_waveform.set('wf_LB')
    awg.ch2_waveform.set('wf_RB')
    

# configure awg

_t_trig_delay=395e-9
# _t_MW_delay=30e-9 # end of CB pulse (<=30ns)
_t_MW_delay=30e-9 # end of CB pulse (<30ns)
t_cb=200e-9
t_sb=600e-9
t_burst=40e-9

station.awg.run_mode.set('TRIG')
station.awg.trigger_impedance.set(50)
station.awg.trigger_level.set(2.5) # for direct input
# station.awg.trigger_level.set(1.2) # for t-split input (scope test)
station.awg.trigger_slope.set('POS')
station.awg.write_raw("TRIG:SEQ:WVAL LAST")


station.psg.pulse_mod_status.set('ON')
station.psg.pulse_mod_trigger_type.set('INT')
station.psg.pulse_mod_internal_trigger.set('FRUN')


# station.psg.pulse_mod_delay.set(_t_trig_delay+t_cb-t_burst-_t_MW_delay) # at end of CB pulse
station.psg.pulse_mod_delay.set(_t_trig_delay-_t_MW_delay) # at beginning of CB pulse
station.psg.pulse_mod_period.set(t_sb+t_cb)
station.psg.pulse_mod_width.set(t_burst)

station.psg.pulse_mod_delay_step.set(0)
station.psg.pulse_mod_period_step.set(0)
station.psg.pulse_mod_width_step.set(0)


inf_pulse(station.awg,t_cb,t_sb)

# station.awg.ch1_state(1)
station.awg.ch2_state(1)

station.awg.run()
station.psg.modulation.set('ON')
station.psg.off()
# station.psg.on()


print('Chs 1 and 2 ON and pulse started')

# send_waveform_to_list
