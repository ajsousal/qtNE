import numpy as np
import pandas as pd
from time import perf_counter,sleep
import json
import os
from datetime import timedelta
from numbers import Number

import csv


# output_index=-1

global prev_state
prev_state=[]
# ind_in_csv=0
prev_val=[]




def callLoops(inner_loop,outer_loop=None,**kwargs):
    if outer_loop:
        outer_loop(inner_loop=inner_loop, **kwargs)
    else:
        inner_loop(**kwargs)



def estimate_measurement_time(loop_size,time_interval,extra_time):
    print('Estimated measurement time (hh:mm:ss): '+ str(timedelta(seconds=loop_size*time_interval+extra_time)))


class dataHandle():

    def __init__(self,data_dict,loop_class,filename=''):

        self.data_dict=data_dict
        self.loop_class=loop_class
        self.filename=filename

        self.filedir=os.path.split(self.filename)[0]

        self.timestable=0
        
        self.ref_time=0
        self.len_array=1


    def add_delay(self,time_delay):

        time_passed=0
        t_i=perf_counter()
        while time_passed<time_delay:
            time_passed=perf_counter()-t_i
        print('waited '+str(time_passed)+' s.')



    def set_Setp(self,parameter,value,type_par,rate=None):

        if rate is None:
            rate=100 # mV
        # print(parameter)
        # self._set_stable(parameter,value,rate)
        parameter.set(value)

        if type_par=='step':
            self.data_dict['setpoints'][0][1]=value[0] if not isinstance(value,Number) else value
            for a in range(len(self.data_dict['combined_step'])):
                self.data_dict['combined_step'][a][1]=parameter.get()[a]
            # print(self.data_dict)

        elif type_par=='sweep':
            self.data_dict['setpoints'][len(self.data_dict['setpoints'])-1][1]=value[0] if not isinstance(value,Number) else value  # the last setpoint, TODO: this only allows for two setpoints
            for a in range(len(self.data_dict['combined_sweep'])):
                self.data_dict['combined_sweep'][a][1]=parameter.get()[a]
            # print(self.data_dict)

    def set_Fixed(self,parameters,values,rate=None):

        if rate is None:
            rate=100

        for par, val in zip(parameters,values):

            # self._set_stable(par,val,rate)
            par.set(val)
            self.data_dict['fixed'][parameters.index(par)][1]=val # if self.len_array==1 else val*np.ones(self.len_array)
            # print(self.data_dict)
            

    def set_Fixed_nosave(self,parameters,values,rate=None):
        if rate is None:
            rate=100

        for par, val in zip(parameters,values):
            # self._set_stable(par,val,rate)
            par.set(val)
            
        self.pars_fixed_to_array=parameters
        self.pars_fixed_vals_to_array=values


    def probe_out_array(self,parameter):
        out_array=parameter.get()
        self.len_array=len(out_array)

    def get_out_array(self,parameter,index,time_factor=1e-6,n_avgs=1): # for use with Keysight digitizer, time-dependent data

        # print(out_array)
            
        out_array=parameter.get()
        # print(out_array)
        print('number of averages: '+ str(n_avgs))
        print('length buffer array: '+str(len(out_array)))
        
        if n_avgs!=1:
            avg_array_size=int(len(out_array)/n_avgs)
            avg_array=np.zeros(avg_array_size)
            for n in  range(n_avgs):
                # print(n)
                # print(len(out_array[n*avg_array_size:(n+1)*avg_array_size]))
                avg_array+=out_array[n*avg_array_size:(n+1)*avg_array_size]/n_avgs    
                
                
            setp_array=np.arange(avg_array_size)*time_factor #2e-9 # in seconds,
            out_array=avg_array 
            # print(len(avg_array))
            # print(len(setp_array))
        else:
        # setp_array=(perf_counter()-self.ref_time) + np.arange(len(out_array))*2e-9 # in seconds
        # time_factor=1e-6 #2e-9
            setp_array=np.arange(len(out_array))*time_factor #2e-9 # in seconds, 
            
        self.data_dict['outputs'][index][1] = out_array

        self.data_dict['setpoints'][len(self.data_dict['setpoints'])-1][1] = setp_array # valid for sweep setpoint

        # print(self.pars_fixed_to_array)
        # print(self.pars_fixed_vals_to_array)
        # for par, val in zip(self.pars_fixed_to_array,self.pars_fixed_vals_to_array):
        #     self.data_dict['fixed'][self.pars_fixed_to_array.index(par)][1] = val*np.ones(len(out_array))        

    def get_out_moku(self,parameter,index): # for use with Keysight digitizer, time-dependent data

        # print(out_array)
            
        out_array=parameter.get()     
        
        self.data_dict['outputs'][index][1] = out_array[1]#[list(out_array.keys())[0]] # assuming one output only
        self.data_dict['setpoints'][len(self.data_dict['setpoints'])-1][1] = out_array[0]#[list(out_array.keys())[1]] # assuming one output only

    def get_Out(self,parameter,index):
        outval = parameter.get()
        # print(outval)
        self.data_dict['outputs'][index][1]=outval
        # print(self.data_dict)
    
    def get_Out_value(self,parameter,index):
        outval = parameter.get()
        # self.data_dict['outputs'][index][1]=outval
        return outval


    def get_Out_avg(self,parameter,index,tavg):
        outval = 0
        time_passed=0
        t_i = perf_counter()

        while time_passed < tavg:
            time_passed=perf_counter()-t_i
            outval += parameter.get()

        print('Aberaged for '+str(time_passed)+' s.')
        self.data_dict['outputs'][index][1]=outval

    def get_Out_avg_value(self,parameter,index,tavg):
        outval = 0
        time_passed=0
        t_i = perf_counter()

        while time_passed < tavg:
            time_passed=perf_counter()-t_i
            outval += parameter.get()

        print('Aberaged for '+str(time_passed)+' s.')

        return outval

    def write_val_to_output(self,index,value):
        self.data_dict['outputs'][index][1]=value

    def get_Out_readout(self,parameter,index,tpulsing,tavg,tmanipulation):

        tstart=perf_counter()
        outval = 0
        cout=0
        time_passed=0

        while (perf_counter()-tstart)<tpulsing:
            t_read=perf_counter()
            while time_passed < tavg:
                cout+=1
                outval += parameter.get()
                time_passed=perf_counter()-t_read

            t_manip=perf_counter()
            while time_passed<tmanipulation:
                time_passed=perf_counter()-t_manip
        
        self.data_dict['outputs'][index][1]=outval/cout
            



    def save_data_db(self):

            ## wrap data in saveable way

            array_data=[]
            for a in self.loop_class.data_dict:
                array_data.append(self.loop_class.data_dict[a])

            array_data_corr = []
            for e1 in array_data:
                for e2 in e1:
                    array_data_corr.append(tuple(e2))


            ## save data on-the-fly
            # print(array_data_corr)

            self.loop_class.datasaver.add_result(*array_data_corr)



    @staticmethod
    def save_data_df_subscriber(result_list,length, state):

        global prev_state
        global prev_val
        
        results_save=state.loop_class.datasaver._dataset._results
        # print(results_save)

        cols_set=list(kk[0].full_name for kk in state.loop_class.data_dict['setpoints'])
        cols_dep=state.loop_class.order_cols

        cols=cols_set+cols_dep

        list_results=[]
        list_vals = np.full(len(cols),np.nan)
        col_trigg=np.zeros(len(cols))
        cdictprevious=[]

        n_setp=len(state.data_dict['setpoints'])

        if results_save:
            # print(results_save)
            # print(prev_state)
            # print(results_save!=prev_state)
            if results_save!=prev_state:
                all_dicts=len(results_save)
                ind_dict=0

                while ind_dict<all_dicts:
                    cdictcurrent=results_save[ind_dict:ind_dict+len(cols_dep)]
                    if cdictcurrent!=cdictprevious:
                        for cdict in cdictcurrent:
                            # print(cdict)
                            for colsp,inds in zip(cols_set,range(0,len(cols_set))):
                                if col_trigg[inds]==0:
                                    list_vals[inds]=cdict[colsp]
                                    col_trigg[inds]+=1
                                    # print(list_vals)
                            
                            for colsd,indd in zip(cols_dep,range(len(cols_set),len(cols))):
                                if col_trigg[indd]==0 and (colsd in cdict):
                                    # print(list_vals)
                                    # print(colsd)
                                    list_vals[indd]=cdict[colsd]
                                    col_trigg[indd]+=1
                                    # print(list_vals)

                        col_trigg=np.zeros(len(cols))
                        list_results.append(list_vals)
                        list_vals=np.full(len(cols),np.nan)

                    ind_dict+=len(cols_dep)
                    # print(ind_dict)

                    cdictprevious=cdictcurrent

            prev_state=results_save

        if state.loop_class.verbose:
            print('\t'.join(map(str,cols)))
            # print(list_results)
            print(*list_results,sep='\n')

        with open(state.filename,'a', newline='\n') as file:
            writer=csv.writer(file,delimiter='\t')
            
            for row in list_results:
                # print(prev_val)
                # print(row[0])
                # print(row[0]!=prev_val)
                if row[0]!=prev_val and n_setp>1:
                    writer.writerow([])
                    writer.writerow(row)
                else:
                    writer.writerow(row)
                prev_val=row[0]



    ############ legacy functions formerly used for saving data to csv - problematic synchronization with dataset data querer

    def finalize_db(self):
        self.save_data_db()
        self.loop_class.datasaver.flush_data_to_database()


    def finalize_df(self):
        '''
        legacy function, replaced by subscriber
        '''
        self.loop_class.run_index_saved.append(self.loop_class.run_index)
        self.add_to_dataset()
        # self.loop_class.run_index_saved=[-1,self.loop_class.run_index]
        # self.add_to_dataset()



    def save_data_df(self, verbose=False):
        '''
        legacy function, replaced by subscriber
        '''

        if perf_counter() - self.loop_class.time_to_save > self.loop_class.datasaver.write_period:
            # print('saving to data')
            self.loop_class.run_index_saved.append(self.loop_class.run_index)
            # print('before save: '+str(self.loop_class.run_index_saved))
            self.add_to_dataset(verbose)
            self.loop_class.run_index_saved=[]
            self.loop_class.run_index_saved.append(self.loop_class.run_index+1)
            # print('after save: '+str(self.loop_class.run_index_saved))
            self.loop_class.time_to_save = perf_counter()


    def add_to_dataset(self, verbose=False): # run_indexes=[last saved index; current index]
        '''
        legacy function, replaced by subscriber
        '''

        run_indexes=self.loop_class.run_index_saved
        empty_line_period=self.loop_class.sweep_size
        # print('in add to dataset:'+str(run_indexes))
        datapanda=self.loop_class.datasaver.dataset.get_data_as_pandas_dataframe(start=run_indexes[0],end=run_indexes[1])    

        dfs_to_save = list()
        for parametername, df in datapanda.items():
            dfs_to_save.append(df)

        df_to_save = pd.concat(dfs_to_save[:len(dfs_to_save)], axis=1)

        df_to_save=df_to_save.reindex(columns=self.loop_class.order_cols)
        
        if verbose:
            print(df_to_save)

        ind_in_db=run_indexes[0]-1
        for kk in range(len(df_to_save)):
            ind_in_db+=1
            if ind_in_db % empty_line_period == 0 and ind_in_db !=0:
                df_to_save.iloc[[kk]].to_csv(path_or_buf=self.filename,mode='a', header=False, sep='\t',line_terminator="\n \n", index_label=False)
            else:
                df_to_save.iloc[[kk]].to_csv(path_or_buf=self.filename,mode='a', header=False, sep='\t', index_label=False)    








class convertedData:


    def __init__(self,datadir) -> None:
        
        self.datadir=datadir


    def initialize_dataset(self, gates, setpoints, setpoints_size, outputs,
                            fixed_dacs=[], combined_sweep=[], combined_step=[], sample=[], comments=[]):




        #### list arrays of data to save, each tuple: (parameter, value_in_loop)
        #### declaration of header


        self.num_setpoints=len(setpoints)
        self.setpoints_size=setpoints_size


        array_data=[]
        data_dict={}


        # starts the header strings for the data file

        self.header_arrayids='# '
        self.header_names='# '
        self.header_shapes='# '


        ## list to reorder columns in output "old" data files

        self.order_cols=[]


        ## setpoint parameters 

        addthis=[]
        setvals=np.zeros(len(setpoints))
        for kk in range(len(setpoints)):
            addthis.append([setpoints[kk], setvals[kk]])
            #
            self.header_arrayids += str(setpoints[kk].full_name) + '_set' + '\t'
            self.header_names += '"' + str(setpoints[kk].name) + '"' + '\t'
            self.header_shapes += str(self.setpoints_size[kk]) + '\t'
            #
            # self.order_cols.append(str(setpoints[kk].full_name))
        data_dict['setpoints']=addthis


        ## outputs

        out_num=len(outputs)
        outvals=np.zeros(out_num)
        addthis=[]
        for kk in range(out_num):
            addthis.append([outputs[kk], outvals[kk]])
            #
            self.header_arrayids += str(outputs[kk]) + '\t'
            self.header_names += '"' + str(outputs[kk].name) + '"' + '\t'
            #
            self.order_cols.append(str(outputs[kk]))
        data_dict['outputs']=addthis


        ## auxiliary parameters 

        # fixed gates

        fixedvals=np.zeros(len(fixed_dacs))
        addthis=[]
        for kk in range(len(fixed_dacs)):
            addthis.append([gates[fixed_dacs[kk]], fixedvals[kk]])
            #
            self.header_arrayids += str(gates[fixed_dacs[kk]].full_name) + '_fix' + '\t'
            self.header_names += '"' + str(gates[fixed_dacs[kk]].name) + '"' + '\t'
            #
            self.order_cols.append(str(gates[fixed_dacs[kk]].full_name))
        data_dict['fixed']=addthis

        # combined gates

        data_dict['combined_sweep']=[]
        combinedsweep_vals=np.zeros(len(combined_sweep))
        addthis=[]
        for kk in range(len(combined_sweep)):
            addthis.append([gates[combined_sweep[kk]], combinedsweep_vals[kk]])
            #
            self.header_arrayids += str(gates[combined_sweep[kk]].full_name) + '_cbsweep' + '\t'
            self.header_names += '"' + str(gates[combined_sweep[kk]].name) + '"' + '\t'
            #
            self.order_cols.append(str(gates[combined_sweep[kk]].full_name))
        data_dict['combined_sweep']=addthis


        data_dict['combined_step']=[]
        combinedstep_vals=np.zeros(len(combined_step))
        addthis=[]
        for kk in range(len(combined_step)):
            addthis.append([gates[combined_step[kk]], combinedstep_vals[kk]])
            #
            self.header_arrayids += str(gates[combined_step[kk]].full_name) + '_cbstep' + '\t'
            self.header_names += '"' + str(gates[combined_step[kk]].name) + '"' + '\t'
            #
            self.order_cols.append(str(gates[combined_step[kk]].full_name))
        data_dict['combined_step']=addthis

        ## wrap the header data with \n

        self.header_arrayids=self.header_arrayids[:len(self.header_arrayids)-1]      # to avoid extra column when generating panda dataframe
        self.header_names=self.header_names[:len(self.header_names)-1]               # to avoid extra column when generating panda dataframe

        self.header_arrayids+='\n'
        self.header_names+='\n'
        self.header_shapes+='\n'


        ### create json snapshot of arrays

        snapshot_parameters={}
        if sample:
            snapshot_parameters.update({'sample': sample})
        if comments:
            snapshot_parameters.update({'comments': comments})

        snapshot_parameters['loop_specs']={}
        snapshot_parameters['arrays']={}

        shapesets=[]
        for kk in range(len(setpoints)):
            shapesets.append(setpoints_size[kk])
            array_id=str(setpoints[kk].full_name)+'_set'
            snapshot_parameters['arrays'][array_id]={}
            snapshot_parameters['arrays'][array_id].update({'name': str(setpoints[kk].name)})
            snapshot_parameters['arrays'][array_id].update({'unit': str(setpoints[kk].unit)})
            snapshot_parameters['arrays'][array_id].update({'label': str(setpoints[kk].label)})
            snapshot_parameters['arrays'][array_id].update({'array_id': array_id})
            snapshot_parameters['arrays'][array_id].update({'shape': shapesets[0:kk+1]})
            snapshot_parameters['arrays'][array_id].update({'is_setpoint': True})

        if len(setpoints)>1:
            snapshot_parameters['loop_specs'].update({'step_id':list(setpoints[0].name) if np.size(setpoints[0].name)>1 else setpoints[0].name})
            snapshot_parameters['loop_specs'].update({'sweep_id':list(setpoints[1].name) if np.size(setpoints[1].name)>1 else setpoints[1].name})
        else:
            snapshot_parameters['loop_specs'].update({'sweep_id':list(setpoints[0].name) if np.size(setpoints[0].name)>1 else setpoints[0].name})


        for kk in range(out_num):
            array_id=str(outputs[kk])
            snapshot_parameters['arrays'][array_id]={}
            snapshot_parameters['arrays'][array_id].update({'name':str(outputs[kk].name)})
            snapshot_parameters['arrays'][array_id].update({'unit':str(outputs[kk].unit)})
            snapshot_parameters['arrays'][array_id].update({'label':str(outputs[kk].label)})
            snapshot_parameters['arrays'][array_id].update({'array_id': array_id})
            snapshot_parameters['arrays'][array_id]['metadata'] = {}
            try:
                snapshot_parameters['arrays'][array_id]['metadata'].update({'wrapped_instrument': str(outputs[kk].instrument.name)})
            except: 
                pass
            snapshot_parameters['arrays'][array_id].update({'shape': shapesets})
            snapshot_parameters['arrays'][array_id].update({'is_setpoint': False})  

        snapshot_parameters['loop_specs'].update({'output_id':list(kk.name for kk in outputs)})

        for kk in range(len(fixed_dacs)):
            array_id=str(gates[fixed_dacs[kk]].full_name)+'_fix'
            snapshot_parameters['arrays'][array_id]={}
            snapshot_parameters['arrays'][array_id].update({'name': str(gates[fixed_dacs[kk]].name)})
            snapshot_parameters['arrays'][array_id].update({'unit': str(gates[fixed_dacs[kk]].unit)})
            snapshot_parameters['arrays'][array_id].update({'label': str(gates[fixed_dacs[kk]].label)})
            snapshot_parameters['arrays'][array_id].update({'array_id': array_id})
            snapshot_parameters['arrays'][array_id].update({'shape': shapesets})
            snapshot_parameters['arrays'][array_id].update({'is_setpoint': False})

        for kk in range(len(combined_sweep)):
            array_id=str(gates[combined_sweep[kk]].full_name)+'_combi'
            snapshot_parameters['arrays'][array_id]={}
            snapshot_parameters['arrays'][array_id].update({'name': str(gates[combined_sweep[kk]].name)})
            snapshot_parameters['arrays'][array_id].update({'unit': str(gates[combined_sweep[kk]].unit)})
            snapshot_parameters['arrays'][array_id].update({'label': str(gates[combined_sweep[kk]].label)})
            snapshot_parameters['arrays'][array_id].update({'array_id': array_id})
            snapshot_parameters['arrays'][array_id].update({'shape': shapesets})
            snapshot_parameters['arrays'][array_id].update({'is_setpoint': False})


        for kk in range(len(combined_step)):
            array_id=str(gates[combined_step[kk]].full_name)+'_combi'
            snapshot_parameters['arrays'][array_id]={}
            snapshot_parameters['arrays'][array_id].update({'name': str(gates[combined_step[kk]].name)})
            snapshot_parameters['arrays'][array_id].update({'unit': str(gates[combined_step[kk]].unit)})
            snapshot_parameters['arrays'][array_id].update({'label': str(gates[combined_step[kk]].label)})
            snapshot_parameters['arrays'][array_id].update({'array_id': array_id})
            snapshot_parameters['arrays'][array_id].update({'shape': shapesets})
            snapshot_parameters['arrays'][array_id].update({'is_setpoint': False})


        snapshot_parameters.update({'formatter': "qcodes.data.gnuplot_format.GNUPlotFormat"})
        snapshot_parameters.update({'io': "<DiskIO, base_location='C:\\\\qtNE_standalone'>"}) ### TODO: modify to retreive base_location from temp


        filenamesnap=os.path.join(self.datadir,'snapshot.json') #"C:\\meas_dbs\\testdata_snapshot.json"


        with open(filenamesnap,'w') as f:
            json.dump(snapshot_parameters, f, indent=4)


        filename=os.path.join(self.datadir,'data.dat')


        with open(filename,'w') as f:
            f.write(self.header_arrayids)
            f.write(self.header_names)
            f.write(self.header_shapes)
            # f.write(self.header_arrayids[2:])

        return data_dict, filename



    def finalize_dataset(self,cols_to_reorder,filename): # obsolete!


        with open(filename, "r") as f:
            df_final=pd.read_table(filename,sep="\t",header=3,index_col=False,names=cols_to_reorder)

        df_final=df_final.reindex(columns=self.order_cols)


        with open(filename,'w') as f:
            f.write(self.header_arrayids)
            f.write(self.header_names)
            f.write(self.header_shapes)

        with open(filename,'a') as f:
            df_final.to_csv(path_or_buf=filename,mode='a', header=False, sep='\t',index=None,line_terminator="\n")
