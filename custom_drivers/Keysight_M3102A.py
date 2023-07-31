import sys
import numpy as np
from functools import partial
from time import perf_counter
from os import path
from qcodes import Instrument
from qcodes.utils.validators import Numbers

try:
    import keysightSD1 as SD1
except:
    import sys
    sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
    import keysightSD1 as SD1


from . import Keysight_fpga_utils as fpga_utils
from qcodes_contrib_drivers.drivers.Keysight.SD_common.SD_DIG import SD_DIG


# class FPGA_parser():
class Keysight_M3102A(SD_DIG):

    def __init__(self, name, chassis=1, slot=5, config_dict={},**kwargs):
            
            super().__init__(name, chassis, slot, channels=4, triggers=4, **kwargs)
        
            DIGI_PRODUCT = "M3102A"                # Product's model number
            # CHASSIS = chassis                      # Chassis number holding product
            # SLOT = slot                        # Slot number of product in chassis
    
            self.bit_depth=15

            self.core=self.SD_AIN()
            # self.core=SD1.SD_AIN()

            # self.open(DIGI_PRODUCT, chassis, slot)

            self.open_with_slot(DIGI_PRODUCT, chassis, slot)
            self.fpga_loaded = 0

            self.channels = config['channels']
            set_settings_DAQconfig(config_dict['DAQconfig'])
            set_settings_channelInputConfig(config_dict['channelInputConfig'])
            set_settings_triggerIOconfig(config_dict['triggerIOconfig'])
            # set_settings_DAQdigitalTriggerConfig(config_dict['DAQdigitalTriggerConfig'])
            # set_settings_FPGAconfig
            

            self.config = config

            def set_settings_DAQconfig(self,configs):
                for ch in self.channels:
                    par_to_set='self.points_per_cycle_'
                    exec('%s',(par_to_set+ch)).set(configs['pointsPerCycle'])
                    par_to_set='self.n_cycles_'
                    exec('%s',(par_to_set+ch)).set(configs['nCycles'])
                    par_to_set='self.DAQ_trigger_delay_'
                    exec('%s',(par_to_set+ch)).set(configs['triggerDelay'])
                    par_to_set='self.DAQ_trigger_mode_'
                    exec('%s',(par_to_set+ch)).set(configs['triggerMode'])

            def set_settings_channelInputConfig(self,configs):

                for ch in self.channels:
                    par_to_set='self.full_scale_'
                    exec('%s',(par_to_set+ch)).set(configs['full_scale'])
                    par_to_set='self.impedance_'
                    exec('%s',(par_to_set+ch)).set(configs['impedance'])
                    par_to_set='self.coupling_'
                    exec('%s',(par_to_set+ch)).set(configs['coupling'])


            def set_settings_triggerIOconfig(self,configs):
                    par_to_set='self.trigger_direction'
                    exec('%s',(par_to_set+ch)).set(configs['direction'])


            # def set_settings_DAQdigitalTriggerConfig(self,configs):
            #     for ch in self.channels:
            #         par_to_set='self.digital_trigger_mode_'
            #         exec('%s',(par_to_set+ch)).set(configs['full_scale'])

            # def set_settings_FPGAconfig(self,configs):


            # def 

    def _waitPointsRead(self,channel,npts):
        timeout=1
        t0=perf_counter()
        totalPointsRead = 0
        while totalPointsRead< npts and perf_counter()-t0 < timeout:
            totalPointsRead= self.core.SD_AIN.DAQcounterRead(channel)
            
        # print('Elapsed '+str(perf_counter()-t0)+' s.')

        
    # def start(self,channel):
    #     self.core.DAQstart(channel)
    #     ## replaced by daq_start
        
    # def flush_buffer(self,channel):
    #     self.core.DAQflush(channel)
    #     ## replaced by daq_flush
        
    def pause(self,channel):
        self.core.SD_AIN.DAQpause(channel)
    
    def resume(self,channel):
        self.core.SD_AIN.DAQresume(channel)
        
    # def stop(self,channel):
    #     self.core.DAQstop(channel)
    #     ## replaced by daq_stop in SD_DIG
        
    # def trigger(self,channel):
    #     self.core.DAQtrigger(channel) 
    #     ## replaced by dac_trigger in SD_DIG

    # def open(self, DIGI_PRODUCT, CHASSIS, SLOT): 
    #     core_id = self.core.SD_AIN.openWithSlot(DIGI_PRODUCT, CHASSIS, SLOT)
        
    #     if core_id < 0:
    #         print("Module open error:", core_id)
    #     else:
    #         print("Module opened:", core_id)
    #         print("Module name:", self.core.getProductName())
    #         print("Slot:", self.core.getSlot())
    #         print("Chassis:", self.core.getChassis())

    # def close(self):
    #     self.core.SD_AIN.close()

####

    def read_buffer_avg(self,channel,npts):
        timeout=1
        self._waitPointsRead(channel,npts)
        daq_data=self.core.DAQread(channel,npts,timeout)
        value=np.mean(daq_data)*self.core.channelFullScale(channel)/2**(self.bit_depth)
        
        return value


    def load_and_config_fpga(self,directory,bitstream_file):
        dig_bitstream = path.join(directory, bitstream_file)

        start = perf_counter()
        fpga_utils.check_error(self.core.FPGAload(dig_bitstream), 'loading dig bitstream')
        duration = (perf_counter() - start) * 1000
        print(f'dig {self.core.getSlot()}: {duration:5.1f} ms')

        self.core.FPGAconfigureFromK7z(dig_bitstream)

        self.fpga_loaded = 1


    def get_fpga_registers(self):
        if self.fpga_loaded:
            fpga_utils.fpga_list_registers(self.core)
        else:
            print('No bitstream loaded to FPGA')

    def fpga_write_to_registerbank(self,registerbank_name,dict_to_write):
        '''
        dict_to_write of the form: {register_name: value, ...}
        '''
        if self.fpga_loaded:
            for entry in dict_to_write:
                fpga_utils.write_fpga(self.core, registerbank_name+'_' + entry, dict_to_write[entry])

        else:
            print('No bitstream loaded to FPGA')


    def fpga_read_registerbank(self,registerbank_name,register_name):
        if self.fpga_loaded:
            value = fpga_utils.read_fpga(self.core, registerbank_name+'_' + register_name)
            # value = value*self.core.channelFullScale(channel)/2**(self.bit_depth) # this is handled at NEInstruments
        else:
            print('No bitstream loaded to FPGA')

        return value