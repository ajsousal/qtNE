import sys
import numpy as np
from functools import partial
from time import perf_counter
from os import path
# from qcodes import Instrument
from qcodes.utils.validators import Numbers

try:
    import keysightSD1 as SD1
except:
    import sys
    sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
    import keysightSD1 as SD1


from . import Keysight_fpga_utils as fpga_utils
from qcodes_contrib_drivers.drivers.Keysight.SD_common.SD_DIG import SD_DIG
from qcodes.instrument import InstrumentModule

# class FPGA_parser():
class Keysight_M3102A(SD_DIG):

    def __init__(self, name, chassis=1, slot=5, **kwargs):
            
        super().__init__(name, chassis, slot, channels=4, triggers=4) #, **kwargs)
    
        DIGI_PRODUCT = "M3102A"                # Product's model number
        # CHASSIS = chassis                      # Chassis number holding product
        # SLOT = slot                        # Slot number of product in chassis

        self._bit_depth = 15

        # self.core=self.SD_AIN()

        # self.open(DIGI_PRODUCT, chassis, slot)

        try:
            self.gain = kwargs['gain']
        except:
            print('Input gain not defined. Setting gain to 1.')

        self.open_with_slot(DIGI_PRODUCT, chassis, slot)
        self.fpga_loaded = 0

        # print(self.kwargs)
        
        self.active_channels = kwargs['active_channels']
        self.set_settings_DAQconfig(kwargs['DAQconfig'])
        self.set_settings_channelInputConfig(kwargs['channelInputConfig'])
        self.set_settings_triggerIOconfig(kwargs['triggerIOconfig'])

        if kwargs['use_fpga']:
            args_fpga = kwargs['FPGAconfig']
            self.FPGAloader = M3102_FPGAloader(parent=self,name='fpga_loader',**args_fpga)
            self.fpga_loaded = 1

        if kwargs['acquisition'] == 'DAQ':
            self.DAQreader = M3102_DAQreader(parent = self,name = 'daq_reader',channels = self.active_channels)
            # self.add_submodule(self.DAQreader)
        elif kwargs['acquisition'] == 'FPGA':
            self.FPGAreader = M3102A_FPGAreader(self,self.active_channels)


        # set_settings_DAQdigitalTriggerConfig(config_dict['DAQdigitalTriggerConfig']) % TODO: config digital trigger
        # set_settings_FPGAconfig
        
        # self.config = config

    def set_settings_DAQconfig(self,configs):
        for ch in range(1,self.n_channels):
            # print(self.__dict__.keys())
            par_to_set='points_per_cycle_'
            self.__dict__['parameters']['%s' %(par_to_set+str(ch))].set(configs['pointsPerCycle'])
            par_to_set='n_cycles_'
            self.__dict__['parameters']['%s' %(par_to_set+str(ch))].set(configs['nCycles'])
            par_to_set='DAQ_trigger_delay_'
            self.__dict__['parameters']['%s' %(par_to_set+str(ch))].set(configs['triggerDelay'])
            par_to_set='DAQ_trigger_mode_'
            self.__dict__['parameters']['%s' %(par_to_set+str(ch))].set(configs['triggerMode'])

    def set_settings_channelInputConfig(self,configs):

        for ch in range(1,self.n_channels):
            par_to_set='full_scale_'
            self.__dict__['parameters']['%s' %(par_to_set+str(ch))].set(configs['fullScale'])
            par_to_set='impedance_'
            self.__dict__['parameters']['%s' %(par_to_set+str(ch))].set(configs['impedance'])
            par_to_set='coupling_'
            self.__dict__['parameters']['%s' %(par_to_set+str(ch))].set(configs['coupling'])


    def set_settings_triggerIOconfig(self,configs):
        self.trigger_direction.set(configs['direction'])


        # def set_settings_DAQdigitalTriggerConfig(self,configs):
        #     for ch in range(self.n_channels):
        #         par_to_set='self.digital_trigger_mode_'
        #         exec('%s',(par_to_set+ch)).set(configs['full_scale'])




            
    ## DAQ operation funcions not included in SD_DIG
    #     
    def pause(self,channel):
        self.SD_AIN.DAQpause(channel)
    
    def resume(self,channel):
        self.SD_AIN.DAQresume(channel)
    ##
    

    # def get_reading_daq(self,channel):
    #     npts=self.SD_AIN.__points_per_cycle[channel]
    #     self.daq_flush(channel)
    #     self.daq_start(channel)
    #     reading = np.mean(self.read_buffer_array(channel, npts))/self.gain
    #     self.daq_stop(channel)

    #     return reading
    
    # def get_reading_daq_array(self,channel, npts):
    #     self.daq_flush(channel) # check, decouple from measurement
    #     self.daq_start(channel) # check, decouple from measurement
    #     daq_array = self.read_buffer_array(channel, npts)/self.gain
    #     self.daq_stop(channel) # check, decouple from measurement

    #     return daq_array

    

class M3102_DAQreader(InstrumentModule):

    def __init__(self, parent, name ,channels):
    
        super().__init__(parent,name)
        
        # self.name = name
        self.module = parent
    
        for n in channels: #range(self.n_channels):
            self.add_parameter(
                'value_daq_{}'.format(n),
                label = 'Value for DAQ {}'.format(n),
                get_cmd = partial(self.read_value, channel = n)
            )

            self.add_parameter(
                'array_daq_{}'.format(n),
                label = 'Value for DAQ {}'.format(n),
                get_cmd = partial(self.read_buffer_array, channel = n)
            )
            
        self.module.add_submodule(name, self)
        

    def read_buffer_array(self, channel):

        npts= self.module._SD_DIG__points_per_cycle[channel] # self.module.SD_AIN.__points_per_cycle[channel]
        timeout=70

        self.module.daq_flush(channel) # check, decouple from measurement
        self.module.daq_start(channel) # check, decouple from measurement

        self._waitPointsRead(channel,npts)
        daq_data=self.module.SD_AIN.DAQread(channel,npts,timeout)
        daq_data=daq_data*self.module.SD_AIN.channelFullScale(channel)/2**(self.module._bit_depth)
        daq_data = daq_data/self.module.gain

        self.module.daq_stop(channel) # check, decouple from measurement
        return daq_data 
    
    def read_value(self,channel):
        return np.mean(self.read_buffer_array(channel))
    

    def _waitPointsRead(self,channel,npts):
        timeout=1
        t0=perf_counter()
        totalPointsRead = 0
        while totalPointsRead< npts and perf_counter()-t0 < timeout:
            totalPointsRead= self.module.SD_AIN.DAQcounterRead(channel)


class M3102_FPGAloader(InstrumentModule):

    def __init__(self, parent, name, bitstream_dir, bitstream_file, active_registers = [], registers_inputs = {},**kwargs):
        '''
            active_register: registers in the loaded FPGA image
            registers_inputs: in case the register accepts user inputs (eg configs), these will be parsed here using config_register()
        '''
        
        super().__init__(parent, name)
        
        # self.name = name
        self.module = parent
        
        self.load_and_config_fpga(bitstream_dir,bitstream_file)
        self.get_fpga_registers()
        

        if active_registers:
            self.active_registers = active_registers
            for reg in self.active_registers:
                print(type(reg))
                self.config_register(reg,registers_inputs[reg])
        
        self.module.add_submodule(name, self)



    def config_register(self,register,config_dict):
        '''
        Configures the registers in the loaded FPGA image. Callable from runtime
        '''
        for par in config_dict:
            self.fpga_write_to_registerbank(register, {par: config_dict[par]})
            print(register)
            print(par)
            self.add_parameter(
                    register+'_'+par,
                    label = 'register',
                    # set_cmd = partial(self.fpga_write_to_registerbank, registerbank_name=register, register_name = par), #(reg, {par: value}), # lambda reg, par, value: self.fpga_write_to_registerbank(reg, {par: value}),
                    set_cmd = partial(self.fpga_write_to_register, registerbank_name=register, register_name = par), #(reg, {par: value}), # lambda reg, par, value: self.fpga_write_to_registerbank(reg, {par: value}),
                    get_cmd = partial(self.fpga_read_registerbank, registerbank_name=register, register_name=par) #lambda reg, par: self.fpga_read_registerbank(reg, par)
                )



    def load_and_config_fpga(self,bitstream_dir,bitstream_file):
        dig_bitstream = path.join(bitstream_dir, bitstream_file)

        start = perf_counter()
        fpga_utils.check_error(self.module.SD_AIN.FPGAload(dig_bitstream), 'loading dig bitstream')
        duration = (perf_counter() - start) * 1000
        print(f'dig {self.module.SD_AIN.getSlot()}: {duration:5.1f} ms')

        self.module.SD_AIN.FPGAconfigureFromK7z(dig_bitstream)

        self.module.fpga_loaded = 1


    def get_fpga_registers(self):
        if self.module.fpga_loaded:
            fpga_utils.fpga_list_registers(self.module.SD_AIN)
        else:
            print('No bitstream loaded to FPGA')


    def fpga_write_to_register(self, value, registerbank_name, register_name):
        fpga_utils.write_fpga(self.module.SD_AIN, registerbank_name+'_' + register_name, int(value)) ## TODO : infer cast from register
        

    def fpga_write_to_registerbank(self,registerbank_name,dict_to_write):
        '''
        dict_to_write of the form: {register_name: value, ...}
        '''
        if self.module.fpga_loaded:
            for entry in dict_to_write:
                print(type(dict_to_write[entry]))
                fpga_utils.write_fpga(self.module.SD_AIN, registerbank_name+'_' + entry, dict_to_write[entry])

        else:
            print('No bitstream loaded to FPGA')


    def fpga_read_registerbank(self,registerbank_name,register_name):
        if self.module.fpga_loaded:
            value = fpga_utils.read_fpga(self.module.SD_AIN, registerbank_name+'_' + register_name)
        else:
            print('No bitstream loaded to FPGA')

        return value



    
## TODO:
class M3102A_FPGAreader():

    def __init__(self, module, channel, registry_bank):

        self.add_parameter(
            'reading_fpga',
            label = 'reading from FPGA',
            get_cmd = partial(self.get_reading_fpga, channel = channel)
        )


    def fpga_read_registerbank(self,registerbank_name,register_name):
        if self.fpga_loaded:
            value = fpga_utils.read_fpga(self.SD_AIN, registerbank_name+'_' + register_name)
        else:
            print('No bitstream loaded to FPGA')

        return value

    def get_reading_fpga(channel,reg_bank,reg):
            self.daq_trigger(channel)
            value = self.fpga_read_registerbank(reg_bank,reg)
            value = value *self.get_full_scale(channel)/2**self._bit_depth/self.gain

            return value

