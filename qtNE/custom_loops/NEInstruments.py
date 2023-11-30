# from numbers import Number
from time import perf_counter, sleep
import qcodes

from shutil import copyfile
from inspect import signature

from numpy import array
from scipy import signal

class NEtransport(object):

    def __init__(self, station, *args, **kwargs):
        # self.station=station
        self.station=station # args[0]

    # Input/Output instruments
    
    class time_machine():
    
        _is_physical_instrument = False
        
        def __init__(self,station):
            self.station=station
            
        def create_parameter(self,dictionary,index):

            parameter = qcodes.Parameter(
                dictionary['IDs'][index],
                label=dictionary['IDs'][index],
                unit=dictionary['unit'],
                get_cmd= perf_counter
            )
            return parameter

    class S3b():

        '''
        Dictionary S3b:
                    "component": instrument name initialized in create_instruments
                    "IDs": DAC name
                    "DAC number":
                    "gains": gain set manually on the module
                    "unit": "mV"
        '''

        _is_physical_instrument = True
        _driver_path = 'qcodes_contrib_drivers.drivers.QuTech.IVVI'

        _parameter_dictionary = {'ID': str,
                                 'DAC number': int,
                                 'gain': float,
                                 'label': str,
                                 'units': str
                                 }

        def __init__(self, station):
            # super().__init__()
            self.station = station
            # print(self.test_variable)

        def create_parameter(self, dictionary, index):

            parameter = qcodes.Parameter(
                dictionary['IDs'][index],
                label=dictionary['IDs'][index],
                unit=dictionary['unit'],
                instrument=self.station[dictionary['component']],
                # self.station[dictionary['component']]._set_dac(dictionary['DAC number'][ind],x/dictionary['gains'][ind]),
                set_cmd=lambda x, ind=index: getattr(self.station[dictionary['component']], 'dac'+str(
                    dictionary['DAC number'][ind])).set(x/dictionary['gains'][ind]),
                # self.station[dictionary['component']]._get_dac(dictionary['DAC number'][ind])*dictionary['gains'][ind]
                get_cmd=lambda ind=index: getattr(self.station[dictionary['component']], 'dac'+str(
                    dictionary['DAC number'][ind])).get()*dictionary['gains'][ind]
            )

            return parameter

    class S2d():

        '''
        Dictionary S2d:
                "component": instrument name initialized in create_instruments
                "IDs": DAC name
                "DAC number":
                "gains": gain set manually on the module
                "unit": "mV"
        '''

        _is_physical_instrument = True
        _driver_path = 'qcodes_contrib_drivers.drivers.QuTech.IVVI'

        def __init__(self, station):
            # super().__init__()
            self.station = station
            # print(self.test_variable)

        def create_parameter(self, dictionary, index):

            parameter = qcodes.Parameter(
                dictionary['IDs'][index],
                label=dictionary['IDs'][index],
                unit=dictionary['unit'],
                instrument=self.station[dictionary['component']],
                # self.station[dictionary['component']]._set_dac(dictionary['DAC number'][ind],x/dictionary['gains'][ind]),
                set_cmd=lambda x, ind=index: getattr(self.station[dictionary['component']], 'dac'+str(
                    dictionary['DAC number'][ind])).set(x/dictionary['gains'][ind]),
                # self.station[dictionary['component']]._get_dac(dictionary['DAC number'][ind])*dictionary['gains'][ind]
                get_cmd=lambda ind=index: getattr(self.station[dictionary['component']], 'dac'+str(
                    dictionary['DAC number'][ind])).get()*dictionary['gains'][ind]
            )

            return parameter

    class SR830():

        '''
        Dictionary S3b:
                "component": instrument name initialized in create_instruments
                "parameters": find names in qcodes driver
                                outputs: (Data transfer section) e.g. 'X', 'Y', 'R', 'P'
                                inputs:  'frequency', 'amplitude', 'phase'
                "labels": labels for each parameter
                "units":
                "init":
        '''

        _is_physical_instrument = True
        _driver_path = 'qcodes.instrument_drivers.stanford_research.SR830'

        def __init__(self, station):
            # super().__init__()
            self.station = station
            # print(self.test_variable)

        def create_parameter(self, dictionary):

            if 'init' in dictionary:
                for config in dictionary['init']:
                    if config == 'sensitivity' and dictionary['init'][config] == 'auto':
                        self.station[dictionary['component']].auto_gain()
                    elif config == 'phase' and dictionary['init'][config] == 'auto':
                        self.station[dictionary['component']].auto_phase()
                    else:
                        getattr(self.station[dictionary['component']], config).set(
                            dictionary['init'][config])

            parameter_list = []

            for param, plabel, punit in zip(dictionary['parameters'], dictionary['labels'], dictionary['units']):
                try:
                    parameter = getattr(
                        self.station[dictionary['component']], param)
                    parameter.label = plabel
                    parameter.unit = punit
                    parameter_list.append(parameter)

                except:
                    print('Parameter '+str(param) +
                          ' not found in SR830 driver.')

            return parameter_list

    class Agilent33250():
        '''
        Dictionary Agilent33250:
                "component": instrument name initialized in create_instruments
                "init": initializes instrument at start of measurement with enclosed settings (see instrument driver)

        '''

        _is_physical_instrument = True
        _driver_path = 'custom_drivers.KeysightAgilent_33XXX'

        def __init__(self, station):
            # super().__init__()
            self.station = station
        # print(self.test_variable)

        def create_parameter(self, dictionary):

            tryit = True
            attempts = 0

            while tryit and attempts < 4:

                try:

                    wf_channel = getattr(self.station[dictionary['component']], dictionary['channel'])

                    if dictionary['init']:

                        if 'sync' in dictionary:
                            self.station[dictionary['component']
                                         ].sync.output(dictionary['sync'])

                        if 'init' in dictionary:
                            for config in dictionary['init']:
                                try:
                                    getattr(wf_channel, config)(
                                        dictionary['init'][config])
                                except:
                                    print('Cannot set '+str(config)+'. Retry.')

                        if dictionary['start']:
                            self.station[dictionary['component']
                                         ].force_trigger()

                        print('Agilent 33250 initialized.')
                        tryit = False

                except:

                    attempts += 1
                    print('WF init error. Retrying '+str(attempts)+'/4.')

                    sleep(5.0)


                if "hocus pocus":
                    wf_channel.output.set('OFF')
                    wf_channel.output.set('ON')
                    self.station[dictionary['component']].write_raw('TRIG')

    # Output instruments

    class Keithley4200():

        '''
        Dictionary Keithley4200:
            "component":  instrument name initialized in create_instruments
            "name": output name (for dataset name)
            "gain": gain set manually in the IVVI I/V converter (not set in the Keithley)
            "label": output label (for plotting)
            "unit": "nA",
        '''

        _is_physical_instrument = True
        _driver_path = ''

        def __init__(self, station):
            # super().__init__()
            self.station = station
        # print(self.test_variable)

        def create_parameter(self, dictionary):

            if 'metaparameters' in dictionary:
                for setting in dictionary['metaparameters']:
                    try:
                        getattr(self.station[dictionary['component']], setting).set(
                            dictionary['metaparameters'][setting])
                    except:
                        print('Error in setting parameter: '+str(setting))

            # function defined because the instrument needs to be triggered before reading value

            def get_reading():
                self.station[dictionary['component']].trigger()
                reading = self.station[dictionary['component']
                                       ]._read_next_value()/dictionary['gain']

                return reading

            parameter = qcodes.Parameter(
                dictionary['name'],
                label=dictionary['label'],
                unit=dictionary['unit'],
                instrument=self.station[dictionary['component']],
                get_cmd=lambda: get_reading()
            )
            return parameter

            # get_cmd = lambda: self.self.station[dictionary['component']]._read_next_value()/dictionary['gain']

    class M3102A():

        '''
        Dictionary for Keysight M3102A digitizer
            "component":  instrument name initialized in create_instruments
            "name": output name (for dataset name)
            "gain": gain set manually in the IVVI I/V converter (not set in the Keithley)
            "label": output label (for plotting)
            "unit": "nA",
        '''

        _is_physical_instrument = True
        _driver_path = 'custom_drivers.Keysight_M3102A'

        _parameter_dictionary = {'ID': str,
                                 'gain': float,
                                 'label': str,
                                 'channel': int,
                                 'units': str
                                 }

        def __init__(self, station):
            # super().__init__()
            self.station = station
            # print(self.test_variable)



        def create_parameter(self, dictionary):

            try:
                self.output_type = dictionary['output']
            except:
                self.output_type = 'value'

                
            def get_reading_daq(channel, npts):
                self.station[dictionary['component']].flush_buffer(channel)
                self.station[dictionary['component']].start(channel)
                if self.output_type == 'value':
                    reading = self.station[dictionary['component']].read_buffer_avg(channel, npts)/dictionary['gain']
                elif self.output_type == 'array':
                    reading = self.station[dictionary['component']].read_buffer_array(channel, npts)/dictionary['gain']

                self.station[dictionary['component']].stop(channel)

                return reading


            def get_reading_fpga(channel,reg_bank,reg):
                self.station[dictionary['component']].trigger(channel)
                value = self.station[dictionary['component']].fpga_read_registerbank(reg_bank,reg)
                value = value *self.fullscale/2**self.bit_depth/dictionary['gain']

                return value

            channel = dictionary['channel']
            self.fullscale = self.station[dictionary['component']].core.channelFullScale(channel)
            self.bit_depth = 15

            # if 'startDAQ' in dictionary and dictionary['startDAQ']:
            #     self.station[dictionary['component']].start(channel)

            if 'metaparameters' in dictionary:

                pointsPerCycle = dictionary['metaparameters']['DAQconfig']['pointsPerCycle']
                nCycles = (1 if dictionary['metaparameters']['DAQconfig']['nCycles'] == -1 else dictionary['metaparameters']['DAQconfig']['nCycles'])

                for setting in dictionary['metaparameters']:
                    setting_dict = dictionary['metaparameters'][setting]
                    
                    if not setting == 'FPGAconfig':
                        
                        if 'channel' in list(signature(getattr(self.station[dictionary['component']].core, setting)).parameters):
                            setting_dict['channel'] = channel

                        try:
                            getattr(self.station[dictionary['component']].core, setting)(**setting_dict)
                        except:
                            print('Error setting function: '+str(setting))

                    elif setting == 'FPGAconfig':
                        
                        self.station[dictionary['component']].load_and_config_fpga(setting_dict['bitstream_dir'],setting_dict['bitstream_file'])

                        if dictionary['acquisition'] == 'FPGA':
                            print('configuring FPGA')

                            self.station[dictionary['component']].get_fpga_registers()

                            self.databank = setting_dict['data_register'][0]
                            self.regdata = setting_dict['data_register'][1]

                            for par in setting_dict['config']:
                                if not setting_dict['config'][par] == 'auto':
                                    self.station[dictionary['component']].fpga_write_to_registerbank(setting_dict['config_register'],{par: setting_dict['config'][par]})
                                else: ## temporary solution, case-specific!
                                    multi_val = round(2**20/setting_dict['config']['period'])
                                    self.station[dictionary['component']].fpga_write_to_registerbank(setting_dict['config_register'],{par: multi_val})



            if dictionary['acquisition'] == 'DAQ':
                print('going to read DAQ')
                parameter = qcodes.Parameter(
                    dictionary['name'],
                    label=dictionary['label'],
                    unit=dictionary['unit'],
                    instrument=self.station[dictionary['component']],
                    get_cmd=lambda ch=channel, npts=pointsPerCycle*nCycles: get_reading_daq(ch, npts)
                )

            elif dictionary['acquisition'] == 'FPGA':
                print('going to read FPGA')
                self.station[dictionary['component']].start(channel) # start DAQ 

                parameter = qcodes.Parameter(
                    dictionary['name'],
                    label=dictionary['label'],
                    unit=dictionary['unit'],
                    instrument=self.station[dictionary['component']],
                    get_cmd=lambda ch = channel, rdatabank=self.databank, regdata=self.regdata: get_reading_fpga(ch,rdatabank,regdata)
                )

            return parameter

    class MokuScope():

            '''
            Dictionary for Moku:Pro
                "component":  instrument name initialized in create_instruments
                "name": output name (for dataset name)
                "gain": gain set manually in the IVVI I/V converter (not set in the Keithley)
                "label": output label (for plotting)
                "unit": "nA",
            '''

            _is_physical_instrument = True
            _driver_path = ''

            _parameter_dictionary = {'ID': str,
                                     'gain': float,
                                     'label': str,
                                     'channel': int,
                                     'units': str
                                     }

            def __init__(self, station):
                # super().__init__()
                self.station = station
                # print(self.test_variable)

                

            def create_parameter(self, dictionary):
                
                self.i = self.station[dictionary['component']].i
                timebase_start = dictionary['metaparameters']['timebase'][0]
                timebase_end = dictionary['metaparameters']['timebase'][1]
                timewindow=timebase_end-timebase_start
                self.i.set_timebase(timebase_start, timebase_end)
                trig_mode = dictionary['metaparameters']['trigger_mode']
                self.i.set_trigger(source='ChannelA',mode=trig_mode)#,holdoff=(timebase_end-timebase_start))
                
                # self.npts_broadcast = (self.i.get_timebase()[list(self.i.get_timebase().keys())[1]]- self.i.get_timebase()[list(self.i.get_timebase().keys())[0]])*self.i.get_samplerate()['sample_rate']

                channel = 'Input'+dictionary['input_ch']
                ch_source = dictionary['metaparameters']['source_ch']
                self.i.set_source(ch_source,channel)
                
                self.npts = 1024
                self.timewindow = timebase_end-timebase_start
                
                self.i.enable_rollmode(False)
                # self.i.set_acquisition_mode('DeepMemory')
                self.i.set_acquisition_mode('Precision')


                def get_reading_buffer():
                    path_to_save = 'C:\\_measurement_software\\qtNE\\tmp'
                    fname_to_save = 'tmp_data.npy'

                    response = self.i.save_high_res_buffer(comments='tmp')
                    fname_memory = response['file_name']
                    self.i.download(target='persist',file_name=fname_to_save,local_path=path_to_save)
                    self.i.delete(target='persist',file_name=fname_memory)
                    data_raw = np.load(os.path.join(path_to_save,fname_to_save))
                    # print(data_raw)
                    data_array = data_raw # [array(data_raw['time']), array(data_raw['ch'+dictionary['input_ch']])/dictionary['gain']]
                    return data_raw


                def get_reading_trace(channel,n_avgs):
                    sleep(timewindow)
                    data_raw = self.i.get_data()
                    data_array = [array(data_raw['time']), array(data_raw['ch'+dictionary['input_ch']])/dictionary['gain']]
                    
                    
                    for i in range(n_avgs-1):
                        print(i)
                        data_raw = self.i.get_data()
                        data_array[1] += array(data_raw['ch'+dictionary['input_ch']])/dictionary['gain']
                        
                        
                    data_array[1]=data_array[1]/n_avgs
                    
                    return data_array

                def get_spectra_density(channel,n_avgs, sample_f):
                    data_timedomain = get_reading_trace(channel,n_avgs)
                    (f,spc) = signal.periodogram(array(data_timedomain[1])/dictionary['gain'],sample_f,scaling='density',detrend=None)
                    data_array = [f, spc]
                    return data_array

                if dictionary['metaparameters']['mode']=='trace':
                    parameter = qcodes.Parameter(
                            dictionary['name'],
                            label=dictionary['label'],
                            unit=dictionary['unit'],
                            instrument=self.station[dictionary['component']],
                            get_cmd=lambda ch=channel, n_avgs=dictionary['metaparameters']['n_avgs']: get_reading_trace(ch,n_avgs)
                        )     
                elif dictionary['metaparameters']['mode']=='spectral_density':
                    parameter = qcodes.Parameter(
                            dictionary['name'],
                            label=dictionary['label'],
                            unit=dictionary['unit'],
                            instrument=self.station[dictionary['component']],
                            get_cmd=lambda ch=channel, n_avgs=dictionary['metaparameters']['n_avgs'], sample_f = self.npts/self.timewindow: get_spectra_density(ch,n_avgs, sample_f)
                        )
                return parameter

# PI controller - charge sensing


class CShires(object):

    def __init__(self,
                 station,
                 inputs,
                 ID_Is,
                 ID_coarse,
                 ID_fine=None,
                 outputs=[]
                 ):

        self.station = station
        self.inputs = inputs
        self.outputs = outputs

        self.ID_Is = ID_Is
        self.ID_coarse = ID_coarse
        self.ID_fine = ID_fine

        self.fun_get_is = lambda: self.outputs[self.ID_Is].get()/1e9
        self.fun_set_v_ps_coarse = lambda x: self.inputs[self.ID_coarse].set(x)
        try:
            self.inputs[self.ID_fine]
            self.fun_set_v_ps_fine = lambda x: self.inputs[self.ID_fine].set(x)
            self.use_fine = True
            self.delta_fine = 98.0

        except:
            self.fun_set_v_ps_fine = lambda x: x
            self.use_fine = False
            print('no fine')
            self.delta_fine = 0.

    def ErrCurr(self, dictionary):

        _is_virtual_instrument = True

        parameter = qcodes.Parameter(
            'ErrCurr',
            label='Error current',
            unit='nA',
            get_cmd=lambda: self.i_s
        )
        return parameter

    def Ac(self, dictionary):

        _is_virtual_instrument = True

        parameter = qcodes.Parameter(
            'Acpar',
            label='Ac',
            unit='a. u.',
            get_cmd=lambda: self.Ac
        )
        return parameter

    def Vfeed(self, dictionary):

        _is_virtual_instrument = True

        if self.ID_fine == None or self.ID_fine == 'None':
            parameter = qcodes.Parameter(
                'Vfeed',
                label='Feedback voltage',
                unit='mV',
                get_cmd=lambda: self.inputs[self.ID_coarse].get()
            )
        else:
            parameter = qcodes.Parameter(
                'Vfeed',
                label='Feedback voltage',
                unit='mV',
                get_cmd=lambda: self.inputs[self.ID_coarse].get(
                ) + self.inputs[self.ID_fine].get()
            )

        return parameter

    def Vcoarse(self, dictionary):

        _is_virtual_instrument = True

        parameter = qcodes.Parameter(
            'Vcoarse',
            label='Feedback voltage',
            unit='mV',
            get_cmd=lambda: self.inputs[self.ID_coarse].get()
        )

        return parameter

    def Vfine(self, dictionary):

        _is_virtual_instrument = True

        parameter = qcodes.Parameter(
            'Vfine',
            label='Feedback voltage',
            unit='mV',
            get_cmd=lambda: self.inputs[self.ID_fine].get()
        )

        return parameter

    def initialize_sensor(self,
                          beta,
                          gamma,
                          V_ps0,
                          bounds,
                          I0,
                          Ac,
                          rangeV=[0, 0],
                          step=0,
                          slope=0):

        _is_virtual_instrument = True

        # Cps, capacitance plunger to set
        # Cpd, capacitance plunger to quantum dot that is sensed
        self.bounds = bounds
        self.V_ps = V_ps0  # initial plunger voltage of the SET
        self.V_pd = None  # plunger voltage of the DOT
        self.Ac = Ac  # Cpd/Cps   #mutual capacitance ratio between plungers of dot and SET. initial values from guess. from measurements
        self.beta = beta
        # 4 megaohm  ,value from Yang, et al.
        self.gamma = gamma  # 80 kiloohm ,value from Yang, et al.
        # self.beta = 4e9       #4 megaohm  ,value from Yang, et al.
        # self.gamma = 80e3         #80 kiloohm ,value from Yang, et al.
        self.I0 = I0  # starting current and operating point, in Amps
        self.i_s = 0

        self.rangeV = rangeV

        # print(self.outputs)
        # print(self.inputs)
        print(self.ID_fine)

        if self.use_fine:
            self.fun_set_v_ps_fine(self.delta_fine)
            self.fun_set_v_ps_coarse(self.V_ps-self.delta_fine)
        else:
            self.fun_set_v_coarse(self.V_ps)

        self.V_ps_begin = V_ps0
        self.Ac_begin = Ac
        self.V_ps_compare = V_ps0

        self.step = step
        self.slope = slope

    def set_compensation(self, V_pd):
        # import ipdb
        import math

        begin_V_ps = self.V_ps_begin
        # print('Begin voltage: %g' % begin_V_ps)
        # print(V_pd)
        # print(self.V_pd)
        if not self.V_pd:
            # print('here')
            self.V_pd = V_pd
            self.V_ps0 = self.V_ps

        print('Vpd: '+str(V_pd))
        print('Start voltage: %g' % self.V_ps0)

        delta_V_pd = self.V_pd - V_pd
        self.V_pd = V_pd  # update the value
        # print(self.V_pd)

        # determine the error current
        Is = self.fun_get_is()
        print('Current before: %g' % Is)
        i_s = Is - self.I0
        # Is - self.I0

        print('Current after: %g' % i_s)

        print('delta: %g' % delta_V_pd)

        Vpsprev = self.V_ps
        print(self.V_ps)

        if abs(delta_V_pd) <= 0.01:
            self.Ac = self.Ac
        else:
            self.V_ps = self.V_ps - self.beta*i_s - delta_V_pd*self.Ac
            self.Ac = self.Ac + self.gamma/delta_V_pd*i_s

        # change the voltage on the SET plunger
        # print self.V_ps
        print('plunger voltage: %s' % self.V_ps)
        # dry run

        # if self.use_fine:
        # delta_fine=18.

        # else:
        # self.delta_fine=0.

        # check if value is still in safe bounds
        low, high = self.bounds
        if self.V_ps > high:
            print('safety engaged, plungergate voltage too high')

            self.fun_set_v_ps_coarse(high+self.delta_fine)
            self.fun_set_v_ps_fine(-self.delta_fine)
            self.V_ps = high

        elif self.V_ps < low:
            print('safety engaged, plungergate voltage too low')

            self.fun_set_v_ps_coarse(low+self.delta_fine)
            self.fun_set_v_ps_fine(-self.delta_fine)
            self.V_ps = low

        else:
            print('OK')

            Vfine = self.V_ps-self.V_ps_compare+self.delta_fine
            print('voltage to fine: %s' % Vfine)

            # if abs(Vfine)<self.delta_fine
            # if abs(Vfine) < self.delta_fine:
            if abs(Vfine) < self.delta_fine+0.2:
                print('here 1')
                self.fun_set_v_ps_fine(Vfine)
            else:
                print('here 2')
                if self.use_fine:
                    Vtocoarse = ((-1)**(1-(self.V_ps+abs(self.V_ps)) /
                                        (2*self.V_ps)))*math.floor(abs(self.V_ps)*10)/10
                    self.fun_set_v_ps_coarse(Vtocoarse)
                    print('voltage to coarse: %s' % Vtocoarse)
                    self.fun_set_v_ps_fine(self.V_ps-Vtocoarse)
                    Vtofine = self.V_ps-Vtocoarse
                    print('voltage to fine: %s' % Vtofine)
                    self.V_ps_compare = Vtocoarse

                else:
                    self.fun_set_v_ps_coarse(self.V_ps)

            # for measurements without sweepback
        begin, end = self.rangeV
        if self.V_pd >= end:  # for ramping down voltage, # # if self.V_pd>=end-0.1: # for ramping up voltage
            self.V_pd = None
            # ramping down slow axis - slope times Vpd stepsize, # # self.V_ps_begin=self.V_ps_begin-0.05*4 #ramping up slow axis - slope times Vpd stepsize
            self.V_ps_begin = self.V_ps_begin+self.slope*self.step
            self.V_ps = self.V_ps_begin  # self.V_ps=self.V_ps_begin+(-0.2*2
            self.fun_set_v_ps_coarse(self.V_ps-self.delta_fine)
            self.fun_set_v_ps_fine(self.delta_fine)
            i_s = 0
            self.Ac = self.Ac_begin

            # for measurements without sweepback

        self.i_s = i_s
        print('Current after: %g' % i_s)


class NEmagnetic(object):

    def __init__(self, station, **kwargs):  # ,inputs,outputs=[]):

        # from qcodes.math.field_vector import FieldVector as FieldVector # outdated qcodes 0.11
        from qcodes.math_utils.field_vector import FieldVector as FieldVector

        self.station = station
        # self.inputs=inputs
        # self.outputs=outputs

        print('Using vector magnet')

        # self.vector=vector

        self.r_val = None
        self.theta_val = None
        self.phi_val = None

        self.act_pars = ['r', 'theta', 'phi']

        # print(station)
        # print(kwargs)
        
        try:
            # self.master = self.station[kwargs['magnet']]
            self.master = self.station[kwargs['vector magnet']]
        except:
            print('error in retrieving instrument id (magnet).')
            pass

        def get_polar(self):

            # self.instrument._get_target_field()
            self.master._get_target_field()

        def set_and_ramp_polar(vector):

            # vect=FieldVector(r=self.r_val,theta=self.theta_val,phi=self.phi_val)
            vect = FieldVector(
                r=vector['r'], theta=vector['theta'], phi=vector['phi'])
            print(vect)

            # instrument._set_target_field(vector)
            # instrument._ramp_simultaneously()
            self.master._set_target_field(vect)
            self.master._ramp_simultaneously()

            while self.master.is_ramping():
                pass

        self.vector = qcodes.Parameter(
            'vector',
            label='vector',
            unit='n.a.',
            set_cmd=lambda v: set_and_ramp_polar(v)
        )

    class MercuryiPS():
        '''
        Dictionary for Mercury iPS

        Returns the magnet class (with all sub-parameters) instead of a single parameter - easier for handling and using in-driver function
        '''

        _is_physical_instrument = True
        _driver_path = 'custom_drivers.MercuryiPS_VISA'

        _type = 'vector magnet'

        def __init__(self, station):
            self.station = station

        def create_parameter(self, dictionary, index):

            self.master = self.station[dictionary['component']]
            self.slave = {}

            # self.vector.instrument=self.station[dictionary['component']]

        # auxiliary functions

            def set_and_ramp(psu, value):

                if psu == 'GRPX' and abs(value) > 0.95:  # NE Triton values
                    print('Bx: Field outside safety range')
                elif psu == 'GRPY' and abs(value) > 0.95:  # NE Triton values
                    print('By: Field outside safety range')
                elif psu == 'GRPZ' and abs(value) > 5.95:  # NE Triton values
                    print('Bz: Field outside safety range')
                else:
                    getattr(self.station[dictionary['component']], psu).field_target.set(
                        value)
                    getattr(
                        self.station[dictionary['component']], psu).ramp_to_target()

                while self.master.is_ramping():
                    pass

            def set_polar_target_upgrade(coord, value):
                print('')

            def set_polar_target(r_val=None, theta_val=None, phi_val=None):

                if r_val:
                    self.r_val = r_val
                    self.station[dictionary['component']].r_target.set(r_val)
                if theta_val:
                    self.theta_val = theta_val
                    self.station[dictionary['component']
                                 ].theta_target.set(theta_val)
                if phi_val:
                    self.phi_val = phi_val
                    self.station[dictionary['component']
                                 ].phi_target.set(phi_val)

            # set configs - ramp rates

            self.station[dictionary['component']].GRPX.field_ramp_rate.set(
                dictionary['init']['x_ramp_rate'])
            self.station[dictionary['component']].GRPY.field_ramp_rate.set(
                dictionary['init']['y_ramp_rate'])
            self.station[dictionary['component']].GRPZ.field_ramp_rate.set(
                dictionary['init']['z_ramp_rate'])

            # create parameter
            if dictionary['coordinates'] == 'cartesian':
                if 'x' in dictionary['IDs'][index]:
                    # parameter=self.station[dictionary['component']].GRPX
                    self.slave[dictionary['IDs'][index]
                               ] = self.station[dictionary['component']].GRPX
                    parameter = qcodes.Parameter(
                        dictionary['IDs'][index],
                        label=dictionary['IDs'][index],
                        unit='T',
                        instrument=self.station[dictionary['component']],
                        set_cmd=lambda x, psu='GRPX': set_and_ramp(psu, x),
                        get_cmd=lambda: self.station[dictionary['component']].GRPX.field.get(
                        )
                    )
                elif 'y' in dictionary['IDs'][index]:
                    # parameter=self.station[dictionary['component']].GRPY
                    self.slave[dictionary['IDs'][index]
                               ] = self.station[dictionary['component']].GRPY
                    parameter = qcodes.Parameter(
                        dictionary['IDs'][index],
                        label=dictionary['IDs'][index],
                        unit='T',
                        instrument=self.station[dictionary['component']],
                        set_cmd=lambda x, psu='GRPY': set_and_ramp(psu, x),
                        get_cmd=lambda: self.station[dictionary['component']].GRPY.field.get(
                        )
                    )
                elif 'z' in dictionary['IDs'][index]:
                    # parameter=self.station[dictionary['component']].GRPZ
                    self.slave[dictionary['IDs'][index]
                               ] = self.station[dictionary['component']].GRPZ
                    parameter = qcodes.Parameter(
                        dictionary['IDs'][index],
                        label=dictionary['IDs'][index],
                        unit='T',
                        instrument=self.station[dictionary['component']],
                        set_cmd=lambda x, psu='GRPZ': set_and_ramp(psu, x),
                        get_cmd=lambda: self.station[dictionary['component']].GRPZ.field.get(
                        )
                    )
                else:
                    print('No valid field component [x,y,z].')

            elif dictionary['coordinates'] == 'spherical':

                if 'r' in dictionary['IDs'][index]:
                    parameter = qcodes.Parameter(
                        dictionary['IDs'][index],
                        label=dictionary['IDs'][index],
                        unit='T',
                        instrument=self.station[dictionary['component']],
                        set_cmd=lambda r: set_polar_target(r_val=r),
                        get_cmd=lambda: self.station[dictionary['component']].r_measured.get(
                        )
                    )
                if 'theta' in dictionary['IDs'][index]:
                    parameter = qcodes.Parameter(
                        dictionary['IDs'][index],
                        label=dictionary['IDs'][index],
                        unit='deg.',
                        instrument=self.station[dictionary['component']],
                        set_cmd=lambda theta: set_polar_target(
                            theta_val=theta),
                        get_cmd=lambda: self.station[dictionary['component']].theta_measured.get(
                        )
                    )
                if 'phi' in dictionary['IDs'][index]:
                    parameter = qcodes.Parameter(
                        dictionary['IDs'][index],
                        label=dictionary['IDs'][index],
                        unit='deg.',
                        instrument=self.station[dictionary['component']],
                        set_cmd=lambda phi: set_polar_target(phi_val=phi),
                        get_cmd=lambda: self.station[dictionary['component']].phi_measured.get(
                        )
                    )

            return parameter


class NErf(object):

    def __init__(self, station, **kwargs):
        self.station = station
        self.sequence_pulse_function = []
        self.sequence_ref_function = []

        try:
            self.pulser = self.station[kwargs['pulser']]
        except:
            print('error in retrieving awg instrument id.')
            pass
        try:
            self.mw = self.station[kwargs['mw']]
        except:
            print('error in retrieving psg instrument id.')
            pass

    def sequence_cloner(self, sequence_path, data_path):

        copyfile(sequence_path, data_path)

    def sequence_loader(self, sequence_path, sequence_name):

        import importlib
        self.sequence_pulse_module = importlib.import_module(sequence_path)
        importlib.reload(self.sequence_pulse_module)

        self.sequence_pulse_function = getattr(
            self.sequence_pulse_module, sequence_name)

    def sequence_cloner_referencing(self, pulse, reference, data_path):
        from os.path import abspath

        copyfile(pulse['sequence_path'], data_path)
        copyfile(reference['sequence_path'], data_path)

    def sequence_loader_referencing(self, pulse, reference):

        import importlib
        self.sequence_pulse_module = importlib.import_module(
            pulse['sequence_path'])
        importlib.reload(self.sequence_pulse_module)

        self.sequence_pulse_function = getattr(
            self.sequence_pulse_module, pulse['sequence_name'])

        self.sequence_reference_module = importlib.import_module(
            reference['sequence_path'])
        importlib.reload(self.sequence_reference_module)

        self.sequence_reference_function = getattr(
            self.sequence_reference_module, reference['sequence_name'])

    class AgilentE8257D():
        '''
        Dictionary for Agilent E8257D
            IDs: frequency, phase, or power (mandatory names)
            component: name of device in create_instruments
        '''

        _is_physical_instrument = True
        _driver_path = 'custom_drivers.AgilentE8257D'

        _type = 'mw'

        def __init__(self, station):
            self.station = station

        def create_parameter(self, dictionary, index):

            self.station[dictionary['component']].status.set(
                dictionary['init']['RF'])

            try:
                self.station[dictionary['component']].modulation.set(
                    dictionary['init']['MOD'])
            except:
                pass

            parameter = qcodes.Parameter(
                dictionary['IDs'][index],
                label=getattr(
                    self.station[dictionary['component']], dictionary['IDs'][index]).label,
                unit=getattr(
                    self.station[dictionary['component']], dictionary['IDs'][index]).unit,
                instrument=self.station[dictionary['component']],
                set_cmd=lambda x: getattr(
                    self.station[dictionary['component']], dictionary['IDs'][index]).set(x),
                get_cmd=lambda: getattr(
                    self.station[dictionary['component']], dictionary['IDs'][index]).get()
            )

            return parameter

    class AWG5014():
        '''
        Dictionary for AWG 5014
            Note:
            for now, no parameters to initialize, control via experiment, instead loading a py file with bb sequence/waveform defined for the experiment
        '''

        _is_physical_instrument = True
        _driver_path = 'qcodes.instrument_drivers.tektronix.AWG5014'

        _type = 'pulser'

        def __init__(self, station):
            # super().__init__(station)
            self.station = station
        # print(self.test_variable)

        def create_parameter(self, dictionary, index):

            print("Using AWG 5014")

            if 'init' in dictionary:
                for config in dictionary['init']:
                    try:
                        getattr(self.station[dictionary['component']], config).set(
                            dictionary['init'][config])
                    except:
                        print('Cannot set '+str(config)+'. Retry.')

            self.pulser = self.station[dictionary['component']]
            # self.seqpath=dictionary['sequence path']
            self.seqpars_ids = dictionary['IDs']
            # self.seqpars={}
            self.seqpars = {}

            def seqpar_wrapper(key, value):
                print('ran this')
                # if key in self.seqpars_ids:
                self.seqpars[key] = value
                print(self.seqpars)

            def seqpar_getter(key):
                return self.seqpars
                # reply=self.seqpars[key]
                # return reply

            parameter = qcodes.Parameter(
                dictionary['IDs'][index],
                label=dictionary['labels'][index],
                unit=dictionary['units'][index],
                instrument=self.station[dictionary['component']],
                # getattr(self.station[dictionary['component']],dictionary['IDs'][index]).set(x),
                set_cmd=lambda x, key=dictionary['IDs'][index]: seqpar_wrapper(
                    key, x),
                # getattr(self.station[dictionary['component']],dictionary['IDs'][index]).get()
                get_cmd=lambda key=dictionary['IDs'][index]: seqpar_getter(key)
            )

            return parameter


class NENoise(object):

    def __init__(self, station, inputs):
        self.station = station

        self.inputs = inputs

        print('Measuring noise')

    def set_parameters(self, npts=100, gate_list=[], V_ranges=[], ramp_rate=100, int_time=1):

        self.npts = npts
        self.gate_list = gate_list
        self.V_ranges = V_ranges
        self.ramp_rate = ramp_rate
        self.int_time = int_time


# for key,value in kwargs.items():
#                 if isinstance(value,dict):
#                     if 'stepsize' in value:
#                         if value['begin'] < value['end']:
#                             #setattr(self,key,
#                             self.seqpars[key]=np.arange(value['begin'],
#                                                         value['end'],
#                                                         value['stepsize'])
#                         elif value['begin'] > value['end']:
#                             #setattr(self,key,
#                             self.seqpars[key]=np.arange(value['begin'],
#                                                         value['end'],
#                                                         -1*value['stepsize'])
#                     elif 'npts' in value:
#                         #setattr(self,key,
#                         self.seqpars[key]=np.linspace(value['begin'],value['end'],value['npts']+1)
#                 else:
#                     #setattr(self,key,
#                     self.seqpars[key]=value
