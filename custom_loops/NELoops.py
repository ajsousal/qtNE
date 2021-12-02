# from numbers import Number
from time import perf_counter, sleep
import source.measurements.measurement_tools as measurement_tools
from numbers import Number
import numpy as np
from os.path import abspath, join


class NELoops():

    def __init__(self, data_dict=[], order_cols=[], datasaver=None, filename='', verbose=False):
        print('Running measurement using NELoops class.')
        print('For live plotting use qtNE DataViewer.')

        self.data_dict = data_dict
        self.datasaver = datasaver

        self.run_index_saved = []
        self.run_index_saved.append(0)
        self.run_index = 0

        self.time_to_save = perf_counter()
        self.order_cols = order_cols

        self.datahandle = measurement_tools.dataHandle(
            data_dict=self.data_dict, loop_class=self, filename=filename)
        self.meas_start = 0

        self.lenstep = 1

        self.verbose = verbose

        self.do_step = 0

        self.datasaver._dataset.subscribe(
            self.datahandle.save_data_df_subscriber, state=self.datahandle)

    def Loop_2D(self, inner_loop=None, step_par=[], step_vals=[],
                sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                outputs=[], sweepback=True, subscriber_delay=0, step_delay=0, integration_delay=0, polarity_stabilization=0, **kwargs):  # -- to call only in a nesting

        self.do_step = 1
        self.lenstep = len(step_vals)
        self.timeloop = perf_counter()
        ind_step = 0

        self.datahandle.set_Fixed(fix_pars, fix_vals)
        if 'NErf' in kwargs:
            try:
                NErf.sequence_cloner(
                    abspath(NErf.sequence_pulse_module.__file__), self.datahandle.filedir)
            except:
                print('No sequence to save.')

        for stepv in step_vals:

            # Editable loop structure

            self.datahandle.set_Setp(step_par, stepv, type_par='step')

            print('subscriber delay: '+str(subscriber_delay)+' s.')
            print('integration delay: '+str(integration_delay)+' s.')

            if ind_step > 0:
                subscriber_delay = 0
                if len(np.shape(step_vals)) == 1:
                    if step_vals[ind_step-1] != 0:
                        if stepv/step_vals[ind_step-1] < 0:  # or
                            print('polarity stabilization delay: ' +
                                  str(polarity_stabilization)+' s.')
                            self.datahandle.add_delay(polarity_stabilization)
                    else:  # step_vals[ind_step-1]==0:
                        # ignore if starting from zero (next point is index 1)
                        if ind_step > 1:
                            print('polarity stabilization delay: ' +
                                  str(polarity_stabilization)+' s.')
                            self.datahandle.add_delay(polarity_stabilization)

                    if step_delay > 0:
                        print('step stabilization delay: ' +
                              str(step_delay)+' s.')
                        self.datahandle.add_delay(step_delay)

            inner_loop(sweep_par=sweep_par, sweep_vals=sweep_vals, fix_pars=fix_pars, fix_vals=fix_vals,
                       outputs=outputs, subscriber_delay=subscriber_delay, integration_delay=integration_delay, **kwargs)

            if sweepback:
                sweep_vals = sweep_vals[::-1]

            ######################################
            ind_step += 1

    def Loop_Idc(self, sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                 outputs=[], subscriber_delay=0, integration_delay=0, averaging_time=0, **kwargs):

        self.sweep_size = len(sweep_vals)
        meas_start = 0

        if self.do_step == 0:
            self.timeloop = perf_counter()
            self.datahandle.set_Fixed(fix_pars, fix_vals)

        for sweep_volt in sweep_vals:
            self.run_index += 1

            # Editable loop structure

            self.datahandle.set_Setp(sweep_par, sweep_volt, type_par='sweep')

            if integration_delay > 0:
                self.datahandle.add_delay(integration_delay)

            for outpar, outind in zip(outputs, range(len(outputs))):
                self.datahandle.get_Out(outpar, outind)

            ######################################

            if self.meas_start == 0:
                self.timeloop = perf_counter()-self.timeloop
                self.meas_start = 1
                measurement_tools.estimate_measurement_time(
                    self.lenstep*self.sweep_size, self.timeloop-self.datahandle.timestable, self.datahandle.timestable)

            self.datahandle.timestable = 0

            self.datahandle.save_data_db()

            if subscriber_delay > 0:
                self.datahandle.add_delay(subscriber_delay)

    def Loop_polarStep(self, inner_loop=None, step_par=[], step_vals=[],
                       sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                       outputs=[], sweepback=True, NEmagnetic=[], subscriber_delay=0, integration_delay=0, averaging_time=0, **kwargs):  # -- to call only in a nest

        print('')

        self.do_step = 1
        self.lenstep = len(step_vals)
        self.timeloop = perf_counter()
        ind_step = 0

        vect_coord = {}

        index = 0
        for fixed in fix_pars:
            if fixed.name in NEmagnetic.act_pars:
                vect_coord[fixed.name] = fix_vals[index]
            index += 1

        self.datahandle.set_Fixed(fix_pars, fix_vals)

        for stepv in step_vals:

            self.datahandle.set_Setp(step_par, stepv, type_par='step')
            vect_coord[step_par.name] = stepv
            print(vect_coord)
            # vector parameter is created (internally) at NEmagnetic when using spherical coordinates
            NEmagnetic.vector.set(vect_coord)

            if ind_step > 0:
                subscriber_delay = 0
            print('subscriber delay: '+str(subscriber_delay))
            print('integration delay: '+str(integration_delay))

            inner_loop(sweep_par=sweep_par, sweep_vals=sweep_vals, fix_pars=fix_pars, fix_vals=fix_vals, outputs=outputs,
                       subscriber_delay=subscriber_delay, integration_delay=integration_delay, averaging_time=averaging_time, **kwargs)
            # self.datahandle.add_delay(60.0)

            if sweepback:
                sweep_vals = sweep_vals[::-1]

            ######################################
            ind_step += 1

    def Loop_2D_pulsing(self, inner_loop=None, step_par=[], step_vals=[], sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                        outputs=[], NErf=[], sweepback=False, subscriber_delay=0, step_delay=0, integration_delay=0, polarity_stabilization=0, averaging_time=0, **kwargs):

        print('Rabi step loop')

        self.do_step = 1
        self.lenstep = len(step_vals)
        self.timeloop = perf_counter()
        ind_step = 0

        self.datahandle.set_Fixed(fix_pars, fix_vals)
        try:
            NErf.sequence_cloner(abspath(NErf.sequence_pulse_module.__file__), join(
                self.datahandle.filedir, 'sequence.py'))
        except:
            print('Sequence not saved.')

        for stepv in step_vals:

            # Editable loop structure

            self.datahandle.set_Setp(step_par, stepv, type_par='step')

            seqpars = step_par.get()
            print(seqpars)
            # sequence function must return total time
            _, _ = NErf.sequence_pulse_function(NErf.pulser, **seqpars)

            NErf.pulser.run()
            print(NErf.pulser.get_state())

            inner_loop(sweep_par=sweep_par, sweep_vals=sweep_vals, fix_pars=fix_pars, fix_vals=fix_vals, outputs=outputs,
                       subscriber_delay=subscriber_delay, integration_delay=integration_delay, averaging_time=averaging_time, NErf=NErf, **kwargs)

            NErf.pulser.stop()

            if sweepback:
                sweep_vals = sweep_vals[::-1]

            ######################################
            ind_step += 1

        NErf.pulser.ch1_state.set(0)
        NErf.pulser.ch2_state.set(0)
        NErf.pulser.ch3_state.set(0)

    def Loop_Idc_pulsing(self, sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                         outputs=[], subscriber_delay=0, integration_delay=0, averaging_time=0, NErf=[], **kwargs):

        self.sweep_size = len(sweep_vals)
        meas_start = 0

        if self.do_step == 0:
            self.datahandle.set_Fixed(fix_pars, fix_vals)
            try:
                NErf.sequence_cloner(
                    abspath(NErf.sequence_pulse_module.__file__), self.datahandle.filedir)
            except:
                print('Not saved.')

        for sweepv in sweep_vals:
            self.run_index += 1

            # Editable loop structure

            self.datahandle.set_Setp(sweep_par, sweepv, type_par='sweep')

            seqpars = sweep_par.get()
            print(seqpars)
            # sequence function must return total time
            _, _ = NErf.sequence_pulse_function(NErf.pulser, **seqpars)

            NErf.pulser.run()

            self.datahandle.add_delay(integration_delay)
            # print('Averaging for '+str(averaging_time)+' s.')

            # self.datahandle.get_Out_avg(outputs[0],0, averaging_time) # to use with repeating average and high nplc
            self.datahandle.get_Out(outputs[0], 0)

            NErf.pulser.stop()

            ######################################

            self.datahandle.timestable = 0

            self.datahandle.save_data_db()

            if subscriber_delay > 0:
                self.datahandle.add_delay(subscriber_delay)

        NErf.pulser.ch1_state.set(0)
        NErf.pulser.ch2_state.set(0)
        NErf.pulser.ch3_state.set(0)

    def Loop_Idc_pulsing_referencing(self, sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                                     outputs=[], subscriber_delay=0, integration_delay=0, averaging_time=0, NErf=[], **kwargs):

        self.sweep_size = len(sweep_vals)
        meas_start = 0

        if self.do_step == 0:
            self.datahandle.set_Fixed(fix_pars, fix_vals)
            NErf.sequence_cloner(
                abspath(NErf.sequence_pulse_module.__file__), self.datahandle.filedir)

        for sweepv in sweep_vals:
            self.run_index += 1

            # Editable loop structure

            self.datahandle.set_Setp(sweep_par, sweepv, type_par='sweep')

            seqpars = sweep_par.get()
            print(seqpars)
            # sequence function must return total time
            _, _ = NErf.sequence_pulse_function(NErf.pulser, **seqpars)

            NErf.pulser.run()
            # NErf.mw.on()
            exec(kwargs['pre_command'])

            self.datahandle.add_delay(integration_delay)
            # print('Averaging MW for '+str(averaging_time)+' s.')

            # out_mw=self.datahandle.get_Out_avg_value(outputs[0],0, averaging_time) # to use with repeating average and high nplc
            out_mw = self.datahandle.get_Out_value(outputs[0], 0)

            NErf.pulser.stop()

            # NErf.mw.off()
            exec(kwargs['referencing_command'])

            NErf.pulser.run()

            self.datahandle.add_delay(integration_delay)
            # print('Averaging REF for '+str(averaging_time)+' s.')

            # out_ref=self.datahandle.get_Out_avg_value(outputs[0],0, averaging_time) # to use with repeating average and high nplc
            out_ref = self.datahandle.get_Out_value(outputs[0], 0)

            NErf.pulser.stop()
            exec(kwargs['post_command'])

            self.datahandle.write_val_to_output(0, out_mw-out_ref)

            ######################################

            self.datahandle.timestable = 0

            self.datahandle.save_data_db()

            if subscriber_delay > 0:
                self.datahandle.add_delay(subscriber_delay)

        NErf.pulser.ch1_state.set(0)
        NErf.pulser.ch2_state.set(0)
        NErf.pulser.ch3_state.set(0)

    def Loop_Idc_referencing(self, sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                             outputs=[], subscriber_delay=0, integration_delay=0, averaging_time=0, NErf=[], **kwargs):

        self.sweep_size = len(sweep_vals)
        meas_start = 0

        if self.do_step == 0:
            self.datahandle.set_Fixed(fix_pars, fix_vals)

        for sweepv in sweep_vals:
            self.run_index += 1

            # Editable loop structure

            self.datahandle.set_Setp(sweep_par, sweepv, type_par='sweep')

            self.datahandle.add_delay(integration_delay)
            # print('Averaging MW for '+str(averaging_time)+' s.')

            exec(kwargs['pre_command'])

            # to use with repeating average and high nplc
            out_mw = self.datahandle.get_Out_avg_value(
                outputs[0], 0, averaging_time)
            # out_mw=self.datahandle.get_Out_value(outputs[0],0)

            exec(kwargs['referencing_command'])

            self.datahandle.add_delay(integration_delay)
            # print('Averaging REF for '+str(averaging_time)+' s.')

            # to use with repeating average and high nplc
            out_ref = self.datahandle.get_Out_avg_value(
                outputs[0], 0, averaging_time)
            # out_ref=self.datahandle.get_Out_value(outputs[0],0)

            exec(kwargs['post_command'])

            self.datahandle.write_val_to_output(0, out_mw-out_ref)

            ######################################

            self.datahandle.timestable = 0

            self.datahandle.save_data_db()

            if subscriber_delay > 0:
                self.datahandle.add_delay(subscriber_delay)

    def Loop_Idc_pulsing_referencing_v2(self, sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                                        outputs=[], subscriber_delay=0, integration_delay=0, averaging_time=0, NErf=[], **kwargs):

        self.sweep_size = len(sweep_vals)
        meas_start = 0

        if self.do_step == 0:
            self.datahandle.set_Fixed(fix_pars, fix_vals)
            # NErf.sequence_cloner_(abspath(NErf.sequence_pulse_module.__file__),NErf.sequence_reference_module.__file__,self.datahandle.filedir)

        for sweepv in sweep_vals:
            self.run_index += 1

            # Editable loop structure

            self.datahandle.set_Setp(sweep_par, sweepv, type_par='sweep')

            seqpars = sweep_par.get()
            print(seqpars)
            if not isinstance(seqpars, dict):
                seqpars = {'sweepval': seqpars}

            # sequence function must return total time
            _, _ = NErf.sequence_pulse_function(
                NErf.pulser, NErf.mw, **seqpars)

            # NErf.pulser.run()
            # NErf.mw.on()

            self.datahandle.add_delay(integration_delay)
            print('Averaging MW for '+str(averaging_time)+' s.')

            # to use with repeating average and high nplc
            out_mw = self.datahandle.get_Out_avg_value(
                outputs[0], 0, averaging_time)

            # NErf.pulser.stop()
            NErf.mw.frequency.set(10.0e9)
            # NErf.mw.off()
            # NErf.pulser.run()

            # _,_=NErf.sequence_reference_function(NErf.pulser,NErf.mw,**seqpars) # sequence function must return total time

            self.datahandle.add_delay(integration_delay)
            print('Averaging REF for '+str(averaging_time)+' s.')

            # to use with repeating average and high nplc
            out_ref = self.datahandle.get_Out_avg_value(
                outputs[0], 0, averaging_time)

            NErf.pulser.stop()

            self.datahandle.write_val_to_output(0, out_mw-out_ref)

            ######################################

            self.datahandle.timestable = 0

            self.datahandle.save_data_db()

            if subscriber_delay > 0:
                self.datahandle.add_delay(subscriber_delay)

        NErf.pulser.ch1_state.set(0)
        NErf.pulser.ch2_state.set(0)
        NErf.pulser.ch3_state.set(0)

    def Loop_CS(self, sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                outputs=[], CShires=[], subscriber_delay=0, **kwargs):

        self.sweep_size = len(sweep_vals)
        meas_start = 0

        if self.do_step == 0:
            self.timeloop = perf_counter()
            self.datahandle.set_Fixed(fix_pars, fix_vals)
            # self.subs_delay=True

        self.CShires = CShires
        if np.size(sweep_vals.shape) > 1:
            self.CShires.rangeV = (
                sweep_vals[0][0], sweep_vals[sweep_vals.shape[0]-1][0])
        else:
            self.CShires.rangeV = (
                sweep_vals[0], sweep_vals[len(sweep_vals)-1])

        for sweep_volt in sweep_vals:
            self.run_index += 1

            # Editable loop structure

            # self.datahandle.set_V(sweep_par,sweep_volt,type_par='sweep')
            self.datahandle.set_Setp(sweep_par, sweep_volt, type_par='sweep')

            Vps = sweep_par.get()[0] if not isinstance(
                sweep_par.get(), Number) else sweep_par.get()
            print(Vps)
            self.CShires.set_compensation(Vps)

            for outpar, outind in zip(outputs, range(len(outputs))):
                self.datahandle.get_Out(outpar, outind)

            ######################################

            if self.meas_start == 0:
                self.timeloop = perf_counter()-self.timeloop
                self.meas_start = 1
                measurement_tools.estimate_measurement_time(
                    self.lenstep*self.sweep_size, self.timeloop-self.datahandle.timestable, self.datahandle.timestable)

            self.datahandle.timestable = 0

            self.datahandle.save_data_db()

            if subscriber_delay > 0:
                self.datahandle.add_delay(subscriber_delay)

        # if self.do_step==0:
        #     self.datahandle.finalize_db()

    def Loop_CSDualLock(self, sweep_par=[], sweep_vals=[], fix_pars=[], fix_vals=[],
                        outputs=[], CShires=[], subscriber_delay=0, integration_delay=0, **kwargs):

        self.sweep_size = len(sweep_vals)
        meas_start = 0

        if self.do_step == 0:
            self.timeloop = perf_counter()
            self.datahandle.set_Fixed(fix_pars, fix_vals)

        # self.CShires = CShires
        if np.size(sweep_vals.shape) > 1:
            CShires.rangeV = (
                sweep_vals[0][0], sweep_vals[sweep_vals.shape[0]-1][0])
        else:
            CShires.rangeV = (
                sweep_vals[0], sweep_vals[len(sweep_vals)-1])

        for sweep_volt in sweep_vals:
            self.run_index += 1

            # Editable loop structure

            # self.datahandle.set_V(sweep_par,sweep_volt,type_par='sweep')
            self.datahandle.set_Setp(sweep_par, sweep_volt, type_par='sweep')

            Vps = sweep_par.get()[0] if not isinstance(
                sweep_par.get(), Number) else sweep_par.get()
            print(Vps)
            CShires.set_compensation(Vps)

            if integration_delay > 0:
                self.datahandle.add_delay(integration_delay)

            for outpar, outind in zip(outputs, range(len(outputs))):
                self.datahandle.get_Out(outpar, outind)

            ######################################

            if self.meas_start == 0:
                self.timeloop = perf_counter()-self.timeloop
                self.meas_start = 1
                measurement_tools.estimate_measurement_time(
                    self.lenstep*self.sweep_size, self.timeloop-self.datahandle.timestable, self.datahandle.timestable)

            self.datahandle.timestable = 0

            self.datahandle.save_data_db()

            if subscriber_delay > 0:
                self.datahandle.add_delay(subscriber_delay)

        # if self.do_step==0:
        #     self.datahandle.finalize_db()

    def Loop_noisesampler(self, NENoise=[], outputs=[], fix_pars=[], fix_vals=[], **kwargs):

        import csv
        import random

        print(NENoise.gate_list)

        filename = self.datahandle.filename
        self.datahandle.set_Fixed(fix_pars, fix_vals)

        row = NENoise.gate_list+['out_mean', 'out_delta', 'out_var']
        print(row)

        with open(filename, 'w', newline='\n') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(row)

        n = 0
        while n < NENoise.npts:

            row = []

            Vval = np.zeros(len(NENoise.gate_list))
            for gate, Vrange, ind in zip(NENoise.gate_list, NENoise.V_ranges, range(len(NENoise.gate_list))):
                Vval[ind] = random.uniform(Vrange[0], Vrange[1])
                print('Selected gate voltages: ' + str(Vval) + '. Ramping...')
                # self.datahandle._set_stable(NENoise.inputs[gate],Vval[ind],NENoise.ramp_rate)
                NENoise.inputs[gate].set(Vval[ind])

            row.extend(Vval)

            print('gates set to: ' + str(Vval) +
                  '. Acquiring data for '+str(NENoise.int_time)+'s.')

            t_int = 0
            t_ini = perf_counter()
            outarray = []
            while t_int < NENoise.int_time:

                # for just one output! replace by for loop
                outarray.append(outputs[0].get())
                t_int = perf_counter()-t_ini

            outmean = np.mean(outarray)
            outvar = np.var(outarray)
            outdelta = np.max(outarray)-np.min(outarray)
            row.extend([outmean, outdelta, outvar])

            with open(filename, 'a', newline='\n') as file:
                writer = csv.writer(file, delimiter='\t')
                writer.writerow(row)

            n += 1

        print('Measurements finished.')
        for gate in NENoise.gate_list:
                    # self.datahandle._set_stable(NENoise.inputs[gate],0,NENoise.ramp_rate)
            NENoise.inputs[gate].set(0)
        print('Done')

    def Loop_noisetime(self, NENoise=[], outputs=[], fix_pars=[], fix_vals=[], **kwargs):

        import csv

        filename = self.datahandle.filename
        self.datahandle.set_Fixed(fix_pars, fix_vals, NENoise.ramp_rate)

        row = ['time', 'output']

        with open(filename, 'w', newline='\n') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(row)

        rows = []
        row = np.zeros(2)
        time_start = perf_counter()
        time = perf_counter()
        while (time-time_start) < NENoise.int_time:
            row[0] = time-time_start
            # just for one output, replace by for loop
            outval = outputs[0].get()
            row[1] = outval
            time = perf_counter()

            with open(filename, 'a', newline='\n') as file:
                writer = csv.writer(file, delimiter='\t')
                writer.writerow(row)

        print('Measurements finished. DACs not set to zero!')
