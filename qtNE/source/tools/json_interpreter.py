import json

import os
import time
import numpy as np

import qcodes

import shutil

import pickle
from tempfile import gettempdir

import logging

from source.tools import tmp_tools as tmp_tools

import source.measurements.parameter_tools as parameter_tools
import source.measurements.measurement_tools as measurement_tools


from qcodes.instrument.parameter import Parameter
from qcodes.dataset.measurements import Measurement

import pandas as pd

from time import perf_counter
from datetime import timedelta

import importlib


class jsonExperiment():

    def __init__(self, station, jsonfile):
        super().__init__()

        self.file = None
        self.loaded_json = None

        tempdata = tmp_tools.read_tmp(tmp_file='tmp')

        self.locatedatadir = tempdata['current_db']
        self.station = station

        self.file_meas_name = jsonfile
        with open(jsonfile, 'r') as file:
            self.file = file
            self.loaded_json = json.load(self.file)

    def run_experiment(self):

        loop_kwargs = {}
        # kwargs to parse into measurement runner, update along the parameters and class initialization
        runner_kwargs = {}

        timestart = perf_counter()

        locatedataday = os.path.join(
            self.locatedatadir, time.strftime('%Y%m%d', time.localtime()))
        locatedata = os.path.join(
            locatedataday, time.strftime('%H%M%S', time.localtime()))

        if not os.path.exists(locatedata):
            os.makedirs(locatedata)

        path_file_meas = os.path.join(locatedata, 'exp_'+time.strftime(
            '%Y%m%d', time.localtime())+'_'+time.strftime('%H%M%S', time.localtime())+'.jsonscript')
        shutil.copyfile(self.file_meas_name, path_file_meas)

        runner_kwargs.update({
            'locatedata_folder': locatedata
        })

        if self.loaded_json['Loops']['use qcodes'] == True:

            self.db_loc = os.path.join(
                locatedataday, 'db_'+time.strftime('%Y%m%d', time.localtime())+'.db')

            qcodes.initialise_or_create_database_at(self.db_loc)

            sample_name = self.loaded_json['Sample name']
            comments = self.loaded_json['Comments']

            exp = qcodes.load_or_create_experiment(experiment_name='dataset_context_manager',
                                                   sample_name=sample_name)

            meas = Measurement(exp=exp, station=self.station)

        loop_module = importlib.import_module(
            self.loaded_json['Loops']['location'])
        loop_class = self.loaded_json['Loops']['class']
        inner_loop = self.loaded_json['Loops']['inner loop']

        try:
            verbose = self.loaded_json['Print data']
        except:
            pass

        # define input parameters - class is defined from json and dictionary with settings is parsed to parameter

        if 'Instruments' in self.loaded_json:

            gates = {}
            instr_to_parent_kwargs = {}

            for inputs in self.loaded_json['Instruments']['Inputs']:
                instr_class = self.loaded_json['Instruments']['Inputs'][inputs]['class']
                instr_module = importlib.import_module(
                    self.loaded_json['Instruments']['Classes'][instr_class]['location'])
                instr_to_parent_kwargs[instr_class] = {}
                if 'init' in self.loaded_json['Instruments']['Classes'][instr_class]:
                    kwargs = self.loaded_json['Instruments']['Classes'][instr_class]['init']
                    instr_to_parent_kwargs[instr_class].update(kwargs)

                # parent_class = getattr(instr_module, instr_class)(self.station)
                parent_class = getattr(instr_module, instr_class)(self.station,**instr_to_parent_kwargs[instr_class])
                instrument_class = getattr(parent_class, inputs)(self.station)
                inputdict = self.loaded_json['Instruments']['Inputs'][inputs]
                try:
                    instr_to_parent_kwargs[instr_class][instrument_class._type] = inputdict['component']
                except:
                    print(instr_class +
                          ' does not have type. Not parsed to parent class.')

                if inputdict['IDs']:
                    for ji in range(len(inputdict['IDs'])):
                        try:
                            b = instrument_class.create_parameter(inputdict, ji)
                        except:
                            del(self.station[inputdict['component']].parameters[inputdict['IDs'][ji]])
                            b = instrument_class.create_parameter(inputdict, ji)
                            # b = getattr(self.station[inputdict['component']],inputdict['IDs'][ji])
                        print(b)
                            
                        gates[inputdict['IDs'][ji]] = b
                        # independent parameter
                        meas.register_parameter(gates[inputdict['IDs'][ji]])
                        
                print(gates)
            ## time parameter
            
        #     time_parameter = qcodes.Parameter(
        #         'time',
        #         label='time',
        #         unit='s',
        #         get_cmd= time.perf_counter
        # )             
        #     gates['time']=time_parameter
        #     meas.register_parameter(gates['time'])
            

            print(instr_to_parent_kwargs)

            # ## Declare setpoint combined gates (if enabled)

            # list setpoints
            params_setpoints = []
            vals_setpoints = []
            setpoints_size = []

            combidacs_sweep = []
            combidacs_step = []

            # Set sweep gate

            if len(self.loaded_json['Experiment']['Sweep loop']['ID']) == 1 or isinstance(self.loaded_json['Experiment']['Sweep loop']['ID'], str):

                print('here!')
                paramname = self.loaded_json['Experiment']['Sweep loop']['ID'] if isinstance(
                    self.loaded_json['Experiment']['Sweep loop']['ID'], str) else self.loaded_json['Experiment']['Sweep loop']['ID'][0]
                # paramsweep = gates[paramname]
                # params_setpoints.append(paramsweep)
                if paramname=='time' or paramname=='frequency':
                    paramsweep = gates[paramname]
                    params_setpoints.append(paramsweep)
                    vals_setpoints.append([])
                    setpoints_size.append(0)
                else:
                    paramsweep = gates[paramname]
                    params_setpoints.append(paramsweep)

                    for inputs in self.loaded_json['Instruments']['Inputs']:
                        for ids in self.loaded_json['Instruments']['Inputs'][inputs]['IDs']:
                            # if paramname==ids and self.loaded_json['Instruments']['Inputs'][inputs]['class']=='NEtransport':
                            if paramname == ids:

                                classname = self.loaded_json['Instruments']['Inputs'][inputs]['class']

                                #range_ind=self.loaded_json['Experiment']['Class settings']['NEtransport']['Voltage ranges'][paramname]
                                range_ind = self.loaded_json['Experiment']['Class settings'][classname]['ranges'][paramname]
                                if 'stepsize' in range_ind:
                                    if range_ind['begin'] < range_ind['end']:
                                        sweepvalues = np.arange(range_ind['begin'],
                                                                # + range_ind['stepsize'],
                                                                range_ind['end'],
                                                                range_ind['stepsize'])
                                    elif range_ind['begin'] > range_ind['end']:
                                        sweepvalues = np.arange(range_ind['begin'],
                                                                # - range_ind['stepsize'],
                                                                range_ind['end'],
                                                                -1*range_ind['stepsize'])
                                elif 'npts' in range_ind:
                                    sweepvalues = np.linspace(
                                        range_ind['begin'], range_ind['end'], range_ind['npts']+1)

                                vals_setpoints.append(sweepvalues)
                                setpoints_size.append(len(sweepvalues))

            else:

                if self.loaded_json['Experiment']['Class settings']['NEtransport']:
                    combidacs_sweep = self.loaded_json['Experiment']['Sweep loop']['ID']
                    combidacs_sweep_address = []
                    combidacs_sweep_gain = []
                    for ii in combidacs_sweep:
                        for inputs in self.loaded_json['Instruments']['Inputs']:
                            inputdict = self.loaded_json['Instruments']['Inputs'][inputs]
                            try:
                                address = inputdict['IDs'].index(ii)
                                combidacs_sweep_address.append(
                                    inputdict['DAC number'][address])
                                combidacs_sweep_gain.append(
                                    inputdict['gains'][address])
                                combidacs_sweep_instrument = inputdict['component']
                                combidacs_sweep_unit = inputdict['unit']
                            except:
                                pass

                    paramsweep = qcodes.Parameter(
                        '_'.join(
                            self.loaded_json['Experiment']['Sweep loop']['ID']),
                        label='_'.join(
                            self.loaded_json['Experiment']['Sweep loop']['ID']),
                        unit=combidacs_sweep_unit,
                        instrument=self.station[combidacs_sweep_instrument],
                        set_cmd=lambda x: parameter_tools._set_combi(
                            self.station[combidacs_sweep_instrument], combidacs_sweep_address, x, combidacs_sweep_gain),
                        get_cmd=lambda: parameter_tools._get_combi(
                            self.station[combidacs_sweep_instrument], combidacs_sweep_address, combidacs_sweep_gain)
                    )

                    combiranges_sweep = []
                    for curr_range in range(len(combidacs_sweep)):

                        range_ind = self.loaded_json['Experiment']['Class settings'][
                            'NEtransport']['ranges'][combidacs_sweep[curr_range]]
                        if 'stepsize' in range_ind:
                            if range_ind['begin'] < range_ind['end']:
                                combiranges_sweep.append(np.arange(range_ind['begin'],
                                                                   # + range_ind['stepsize'],
                                                                   range_ind['end'],
                                                                   range_ind['stepsize']))
                            if range_ind['begin'] > range_ind['end']:
                                combiranges_sweep.append(np.arange(range_ind['begin'],
                                                                   # - range_ind['stepsize'],
                                                                   range_ind['end'],
                                                                   -1*range_ind['stepsize']))
                        elif 'npts' in range_ind:
                            combiranges_sweep.append(np.linspace(
                                range_ind['begin'], range_ind['end'], range_ind['npts']+1))

                    sweepvalues = parameter_tools.sweepcombined(
                        len(combidacs_sweep), *combiranges_sweep)
                    # independent parameter
                    meas.register_parameter(paramsweep)
                    params_setpoints.append(paramsweep)
                    vals_setpoints.append(sweepvalues)
                    setpoints_size.append(len(combiranges_sweep[0]))

                    for kk in range(len(combidacs_sweep)):
                        meas.unregister_parameter(gates[combidacs_sweep[kk]])
                        meas.register_parameter(
                            gates[combidacs_sweep[kk]], setpoints=tuple(params_setpoints))

            runner_kwargs.update({
                'sweep_par': params_setpoints[0],
                'sweep_vals': vals_setpoints[0]
            })

            enable_sweepback = self.loaded_json['Experiment']['Sweep loop']['sweepback']
            runner_kwargs.update({
                'sweepback': enable_sweepback
            })

            # Set step gate

            if self.loaded_json['Experiment']['Step loop']['to use']:

                if len(self.loaded_json['Experiment']['Step loop']['ID']) == 1 or isinstance(self.loaded_json['Experiment']['Step loop']['ID'], str):
                    paramname = self.loaded_json['Experiment']['Step loop']['ID'] if isinstance(
                        self.loaded_json['Experiment']['Step loop']['ID'], str) else self.loaded_json['Experiment']['Step loop']['ID'][0]
                    paramstep = gates[paramname]
                    params_setpoints.insert(0, paramstep)

                    # if self.loaded_json['Experiment']['Class settings']['NEtransport']:
                    for inputs in self.loaded_json['Instruments']['Inputs']:
                        for ids in self.loaded_json['Instruments']['Inputs'][inputs]['IDs']:
                                # if paramname==ids and self.loaded_json['Instruments']['Inputs'][inputs]['class']=='NEtransport':
                            if paramname == ids:

                                classname = self.loaded_json['Instruments']['Inputs'][inputs]['class']
                                # range_ind = self.loaded_json['Experiment']['Voltage ranges'][paramname]
                                range_ind = self.loaded_json['Experiment']['Class settings'][classname]['ranges'][paramname]
                                if 'stepsize' in range_ind:
                                    if range_ind['begin'] < range_ind['end']:
                                        stepvalues = np.arange(range_ind['begin'],
                                                               # + range_ind['stepsize'],
                                                               range_ind['end'],
                                                               range_ind['stepsize'])
                                    elif range_ind['begin'] > range_ind['end']:
                                        stepvalues = np.arange(range_ind['begin'],
                                                               # - range_ind['stepsize'],
                                                               range_ind['end'],
                                                               -1*range_ind['stepsize'])
                                elif 'npts' in range_ind:
                                    stepvalues = np.linspace(
                                        range_ind['begin'], range_ind['end'], range_ind['npts']+1)

                                vals_setpoints.insert(0, stepvalues)
                                setpoints_size.insert(0, len(stepvalues))

                else:

                    if self.loaded_json['Experiment']['Class settings']['NEtransport']:

                        combidacs_step = self.loaded_json['Experiment']['Step loop']['ID']
                        combidacs_step_address = []
                        combidacs_step_gain = []
                        for ii in combidacs_step:
                            for inputs in self.loaded_json['Instruments']['Inputs']:
                                inputdict = self.loaded_json['Instruments']['Inputs'][inputs]
                                try:
                                    address = inputdict['IDs'].index(ii)
                                    combidacs_step_address.append(
                                        inputdict['DAC number'][address])
                                    combidacs_step_gain.append(
                                        inputdict['gains'][address])
                                    combidacs_step_instrument = inputdict['component']
                                    combidacs_step_unit = inputdict['unit']
                                except:
                                    pass

                        paramstep = qcodes.Parameter(
                            '_'.join(
                                self.loaded_json['Experiment']['Step loop']['ID']),
                            label='_'.join(
                                self.loaded_json['Experiment']['Step loop']['ID']),
                            unit=combidacs_step_unit,
                            instrument=self.station[combidacs_step_instrument],
                            set_cmd=lambda x: parameter_tools._set_combi(
                                self.station[combidacs_step_instrument], combidacs_step_address, x, combidacs_step_gain),
                            get_cmd=lambda: parameter_tools._get_combi(
                                self.station[combidacs_step_instrument], combidacs_step_address, combidacs_step_gain)
                        )

                        combiranges_step = []
                        for curr_range in range(len(combidacs_step)):
                            # range_ind = self.loaded_json['Experiment']['Voltage ranges'][combidacs_step[curr_range]]#['gate '+str(curr_range+1).zfill(2)]
                            range_ind = self.loaded_json['Experiment']['Class settings'][
                                'NEtransport']['ranges'][combidacs_step[curr_range]]
                            if 'stepsize' in range_ind:
                                if range_ind['begin'] < range_ind['end']:
                                    combiranges_step.append(np.arange(range_ind['begin'],
                                                                      # + range_ind['stepsize'],
                                                                      range_ind['end'],
                                                                      range_ind['stepsize']))
                                elif range_ind['begin'] > range_ind['end']:
                                    combiranges_step.append(np.arange(range_ind['begin'],
                                                                      # - range_ind['stepsize'],
                                                                      range_ind['end'],
                                                                      -1*range_ind['stepsize']))
                            elif 'npts' in range_ind:
                                combiranges_step.append(np.linspace(
                                    range_ind['begin'], range_ind['end'], range_ind['npts']+1))

                        stepvalues = parameter_tools.sweepcombined(
                            len(combidacs_step), *combiranges_step)
                        # independent parameter
                        meas.register_parameter(paramstep)
                        params_setpoints.insert(0, paramstep)
                        vals_setpoints.insert(0, stepvalues)
                        setpoints_size.insert(0, len(combiranges_step[0]))

                        for kk in range(len(combidacs_step)):
                            meas.unregister_parameter(
                                gates[combidacs_step[kk]])
                            meas.register_parameter(
                                gates[combidacs_step[kk]], setpoints=tuple(params_setpoints))

                runner_kwargs.update({
                    'step_par': params_setpoints[0],
                    'step_vals': vals_setpoints[0],
                    'sweep_par': params_setpoints[1],
                    'sweep_vals': vals_setpoints[1]
                })
                
                print(runner_kwargs)

            # fixed gates
            # not needed! fix later
            if self.loaded_json['Experiment']['Class settings']['NEtransport']:

                fixeddacs = []  # names
                fixxeddacs_pars = []  # parameters
                fixeddacvolts = []  # values
                for classloop in self.loaded_json['Experiment']['Class settings']:
                    print(classloop)
                    try:
                        for gateloop in self.loaded_json['Experiment']['Class settings'][classloop]['ranges']:
                            if self.loaded_json['Experiment']['Class settings'][classloop]['ranges'][gateloop]['begin'] == self.loaded_json['Experiment']['Class settings'][classloop]['ranges'][gateloop]['end']:
                                fixeddacs.append(gateloop)
                                fixeddacvolts.append(
                                    self.loaded_json['Experiment']['Class settings'][classloop]['ranges'][gateloop]['begin'])
                                meas.unregister_parameter(gates[gateloop])
                                meas.register_parameter(
                                    gates[gateloop], setpoints=tuple(params_setpoints))
                                fixxeddacs_pars.append(gates[gateloop])
                    except:
                        print('Class '+str(classloop)+' has no swept variables.')

                runner_kwargs.update({
                    'fix_pars': fixxeddacs_pars,
                    'fix_vals': fixeddacvolts
                })

            # initalize extra classes and wrap them so that they can be parsed to loop ------------------------>>>>>> maybe this can be moved to the place of parameter init, to avoid explicitly declaring inputs and outputs

            classes_instr = {}
            class_init_kwargs = {}

            setlist = []

            # classes_instr.update({'NEtransport': instrument})

            for classes in self.loaded_json['Instruments']['Classes']:
                class_module = importlib.import_module(
                    self.loaded_json['Instruments']['Classes'][classes]['location'])
                class_init_kwargs.update({'station': self.station})

                # if classes != 'NEtransport':
                try:
                    class_init_kwargs.update(
                        instr_to_parent_kwargs[classes])

                except:
                    print('Class '+str(classes) +
                            ' not in use by any instrument.')

                if 'inputs' in getattr(class_module, classes).__init__.__code__.co_varnames:
                    class_init_kwargs.update({'inputs': gates})
                # if 'parameters needed' in self.loaded_json['Instruments']['Classes'][classes]:
                # 	if 'inputs' in self.loaded_json['Instruments']['Classes'][classes]['parameters needed']:
                # 		class_init_kwargs.update({'inputs': gates})

                if 'init' in self.loaded_json['Instruments']['Classes'][classes]:

                    class_init_kwargs.update(
                        self.loaded_json['Instruments']['Classes'][classes]['init'])

                    for kwarg in self.loaded_json['Instruments']['Classes'][classes]['init']:
                        if 'ID' in kwarg:
                            setlist.append(
                                self.loaded_json['Instruments']['Classes'][classes]['init'][kwarg])

                    # new method, automatic approach

                class_ = getattr(class_module, classes)(**class_init_kwargs)
                classes_instr.update({classes: class_})

            # register outputs, check via meas._interdeps(.dependencies(parambasespec))

            outputs = []
            outdict = {}

            for output in self.loaded_json['Instruments']['Outputs']:

                outfunc = output.partition('_')[2] if output.partition('_')[
                    2] else output
                print(outfunc)

                classinstr = getattr(classes_instr[self.loaded_json['Instruments']['Outputs'][output]['class']], outfunc)(self.station)
                if hasattr(classinstr,'create_parameter'):
                    try:
                        add_output = classinstr.create_parameter(self.loaded_json['Instruments']['Outputs'][output])
                    except:
                        del(self.station[self.loaded_json['Instruments']['Outputs'][output]['component']].parameters[self.loaded_json['Instruments']['Outputs'][output]['name']])
                        add_output = classinstr.create_parameter(self.loaded_json['Instruments']['Outputs'][output])
                        
                    
                else:
                    add_output = getattr(classes_instr[self.loaded_json['Instruments']['Outputs'][output]['class']], outfunc)(self.loaded_json['Instruments']['Outputs'][output])


                if not isinstance(add_output, list):
                    add_output = [add_output]

                for each_output in add_output:
                    print('output: '+str(each_output))
                    outputs.append(each_output)
                    meas.register_parameter(
                        each_output, setpoints=tuple(params_setpoints))
                    outdict.update({each_output.name: each_output})

            runner_kwargs.update({
                'outputs': outputs
            })

            for classes in self.loaded_json['Instruments']['Classes']:
                class_module = importlib.import_module(
                    self.loaded_json['Instruments']['Classes'][classes]['location'])
                if classes != 'NEtransport':
                    if 'outputs' in getattr(class_module, classes).__init__.__code__.co_varnames:
                        classes_instr[classes].outputs = outdict
                # if 'outputs' in getattr(class_module, classes).__init__.__code__.co_varnames:
                        # classes_instr[classes].outputs = outdict
                        
                        
                    # if 'parameters needed' in self.loaded_json['Instruments']['Classes'][classes]:
                    # 	if 'outputs' in self.loaded_json['Instruments']['Classes'][classes]['parameters needed']:
                    # 		classes_instr[classes].outputs=outdict

            # register supporting instruments (to be initialized before meas.run). NOTE: settings not saved to snapshot!

            if 'Supporting Instruments' in self.loaded_json['Instruments']:
                for support in self.loaded_json['Instruments']['Supporting Instruments']:

                    print('Loading support')
                    support_func = support.partition('_')[2] if support.partition('_')[2] else support
                    class_support= getattr(classes_instr[self.loaded_json['Instruments']['Supporting Instruments'][support]['class']], support_func)(self.station)
                    class_support.create_parameter(self.loaded_json['Instruments']['Supporting Instruments'][support])
                    print('Loaded support')

            # initialize data set and data files

            if self.loaded_json['Data saving']['use datahandler'] == True:
                data_to_viewer = measurement_tools.convertedData(
                    datadir=locatedata)

                data_dict, filename = data_to_viewer.initialize_dataset(gates=gates, setpoints=params_setpoints, setpoints_size=setpoints_size, outputs=outputs,
                                                                        fixed_dacs=fixeddacs, combined_sweep=combidacs_sweep, combined_step=combidacs_step, sample=sample_name, comments=comments)

                loop_kwargs.update({'data_dict': data_dict,
                                    'order_cols': data_to_viewer.order_cols,
                                    'filename': filename,
                                    'verbose': verbose})

        # extract instruments from station in case Instruments dictionary is not used

        if not 'Instruments' in self.loaded_json:

            for aa in self.station.components:
                # print(aa)
                # print(self.station.components[aa])
                vars()[aa] = self.station.components[aa]
                instruments_dict = self.station.components
                runner_kwargs.update({'instruments_dict': instruments_dict})

        # initalize extra classes and wrap them so that they can be parsed to loop

        # try:
        for classes in self.loaded_json['Experiment']['Class settings']:
            # print(classes)
            # if classes != 'NEtransport':
            class_ = classes_instr[classes]
            # print(class_)

            for classfunc in self.loaded_json['Experiment']['Class settings'][classes]:
                if classfunc != 'ranges':
                    sets = self.loaded_json['Experiment']['Class settings'][classes][classfunc]
                    # print(sets)
                    getattr(class_, classfunc)(**sets)

            runner_kwargs.update({classes: class_})
        # except:
        # 	print('Class '+str(classes)+' not parsed to kwargs.')
            # pass

        # print(runner_kwargs)

        # clean-up parameters (DACs) registered to measurement

        for inputs in self.loaded_json['Instruments']['Inputs']:
            for parameter in self.loaded_json['Instruments']['Inputs'][inputs]['IDs']:
                if not any(parameter in lst for lst in [(setp.name for setp in params_setpoints), combidacs_sweep, combidacs_step, fixeddacs, (setname for setname in setlist)]):
                    print(parameter)
                    meas.unregister_parameter(gates[parameter])

        # run measurement using caller functions

        if self.loaded_json['Loops']['use qcodes'] == True:

            # meas.write_period = 0.001 # in seconds --- keep at minimum for full data save - fix in the future with finalize function: # datasaver.dataset.get_values('ivvi_VSDe')
            meas.write_period = self.loaded_json['Data saving']['rate']
            if meas.write_period > 1:
                print('WARNING: write period too long. Some data points may be lost.')

            # global datasaver

            with meas.run() as self.datasaver:

                loop_kwargs.update({'datasaver': self.datasaver})

                # parse data dictionary to the class handling the loops (NELoops)
                loop = getattr(loop_module, loop_class)(**loop_kwargs)

                if self.loaded_json['Experiment']['Step loop']['to use']:
                    outer_loop = self.loaded_json['Loops']['outer loop']
                    runner_kwargs.update(
                        {'outer_loop': getattr(loop, outer_loop)})

                runner_kwargs.update({'inner_loop': getattr(loop, inner_loop)})

                try:
                    for key in self.loaded_json['Averaging']:
                        runner_kwargs.update(
                            {key: self.loaded_json['Averaging'][key]})
                except:
                    pass
                # to remove, use Averaging dictionary instead
                if 'delays' in self.loaded_json['Loops']:

                    for delay in self.loaded_json['Loops']['delays']:
                        print(delay)
                        runner_kwargs.update(
                            {delay: self.loaded_json['Loops']['delays'][delay]})

                else:

                    try:
                        runner_kwargs.update(
                            {'subscriber_delay': self.loaded_json['Loops']['subscriber delay']})
                    except:
                        pass
                    try:
                        runner_kwargs.update(
                            {'integration_delay': self.loaded_json['Loops']['integration delay']})
                    except:
                        pass
                try:
                    runner_kwargs.update(
                        {'averaging_time': self.loaded_json['Loops']['averaging_time']})
                except:
                    pass

                ########
                measurement_tools.callLoops(**runner_kwargs)

        else:

            # parse data dictionary to the class handling the loops (NELoops)
            loop = getattr(loop_module, loop_class)(**loop_kwargs)

            if 'outer loop' in self.loaded_json['Loops']:
                outer_loop = self.loaded_json['Loops']['outer loop']
                runner_kwargs.update({'outer_loop': getattr(loop, outer_loop)})

            runner_kwargs.update({'inner_loop': getattr(loop, inner_loop)})

            measurement_tools.callLoops(**runner_kwargs)

        print('Elapsed time (hh:mm:ss): ' +
              str(timedelta(seconds=perf_counter()-timestart)))
