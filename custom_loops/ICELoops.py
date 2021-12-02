import time
import os

from QTMtoolbox_master.functions import qtmlab

class ICELoops():

    def __init__(self):
        print('Running measurement using ICELoops class.')



    def RT_Field(self,instruments_dict, meas_list, dtw, magnet_instrument, variable, setpoint, 
                 rate,**kwargs):
                 
        for arg in kwargs:
            # print(arg)
            # print(kwargs[arg])
            globals()[arg]=kwargs[arg]
            
        # print(locatedata_folder)
        meas_dict = qtmlab.generate_meas_dict(instruments_dict, meas_list)
        
        qtmlab.meas_dict = meas_dict
        qtmlab.dtw = dtw
        
        magnet_instrument.write_rate(0.12)

        # Approach from above
        qtmlab.move(magnet_instrument, variable, setpoint, rate)
        time.sleep(10)
        magnet_instrument.write_fvalue(0)
        
        field_values = np.linspace(begin, end, number_points)
        
        for fval in field_values:
            # Ramp magnet while heating to save time
            # Don't move (blocks python), but rather set rate (see above) and give setpoint
            magnet_instrument.write_fvalue(fval)
            self.heat_triton_to_1p2K(triton_instrument)
            filename=os.path.join(locatedata_folder,'V-BST113-114_Rxx_cooldown_from_above_' + str(fval) + 'T.csv')
            qtmlab.record(2, 1000, filename, silent=True)
            
        magnet_instrument.write_fvalue(0)
        
        
        
    def heat_triton_to_1p2K(self,triton_instrument):
        print('Heating Triton:')
        print('   Close PID loop')
        triton_instrument.loop_on()
        time.sleep(10)
        # After turning on the loop, somehow the setpoint can be changed by the
        # LakeShore software itself (setpoint = current temp value)
        # Hence, afterwards update setpoint.
        print('   Reading setpoint')
        y = True
        while y:
            x = float(triton_instrument.read_PID8())
            if x == 1.2:
                print('   Setpoint is already 1.2 K')
                time.sleep(3)
                y = False
            else:
                print('   Setpoint was' + str(x) + ' K. Changing to 1.2 K')
                triton_instrument.write_PID8(1.2)
                time.sleep(3)
        # The range can also be changed by the LakeShore software, so update it
        # afterwards as well
        print('   Set range to 10 mA')
        triton_instrument.write_range(10)
        time.sleep(3)
        qtmlab.waitfor(triton_instrument, 'temp8', 1.2, 0.2, 120)
        print('   Turn off PID loop')
        triton_instrument.loop_off()
        time.sleep(5)
    
    
    
    def IV_test(self,instruments_dict,meas_list,dtw,ivvi_instrument,keith_instrument,**kwargs):
        
        for arg in kwargs:
            # print(arg)
            # print(kwargs[arg])
            globals()[arg]=kwargs[arg]
        print(locatedata_folder)
        
        meas_dict = qtmlab.generate_meas_dict(instruments_dict, meas_list)
        qtmlab.meas_dict = meas_dict
        qtmlab.dtw = dtw
        
        # filename=os.path.join(locatedata_folder,'data.dat')
        filename='datatest.dat'
        qtmlab.sweep(ivvi_instrument, variable, start, stop, rate, npoints, filename, sweepdev, md=None, scale='lin')
        
    