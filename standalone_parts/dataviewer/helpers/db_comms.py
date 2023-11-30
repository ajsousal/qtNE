import qcodes as qc
import datetime

_date_format_string = "%Y%m%d" 
_time_format_string = "%H%M%S"


_old_data_rule = True

data_dir = "C:\qtNE_dbs_2021\Antonio"

def get_databases(data_dir):
    '''
    Returns list of paths to databases within data_dir
    Args:
        - data_dir: directory where to look for qcodes dbs
    Returns:
        - db_dir_list: list of directories of found qcodes dbs
    '''

    _db_dir_list = qc.dataset.guids_from_dir(data_dir) # returns ({db path --> guid}, (guid --> db path))
    db_dir_list = list(_db_dir_list[0].keys())

    return db_dir_list
#
def get_experiments_from_db(db_dir):
    '''
    Returns experiments in db and list with the start date
    Args:
        - db_dir: directory of database
    Returns:
        - experiments
        - experiments_dates:
    '''

    active_db = db_dir
    db_connection = qc.dataset.connect(active_db)

    experiments = qc.dataset.experiments(db_connection)
    
    experiments_dates = []
    for experiment in experiments:
        experiment_timestamp = experiment.started_at
        experiment_date = datetime.date.fromtimestamp(experiment_timestamp)
        experiments_dates.append(experiment_date.strftime(_date_format_string))

    return experiments, experiments_dates




    # experiment = experiments[0] # TODO: replace with for loop 
    # for experiment in experiments:



def get_ds_from_experiment(experiment, run_id):
    '''
    Returns data_set with run_id
    '''

# _num_runs_experiment = experiment.last_counter #last_data_set().run_id
# for _run_id in range(_num_runs_experiment):
    ds = experiment.data_sets()[run_id]
    
    ds_timestamp_str = ds.run_timestamp() #(_run_id).run_timestamp()
    if not ds_timestamp_str:
        ds_timestamp_str = '1990-01-01 00:00:00'
    ds_timestamp = datetime.datetime.strptime(ds_timestamp_str,"%Y-%m-%d %H:%M:%S") 
    ds_time = ds_timestamp.strftime(_time_format_string)
    # print(ds_timestamp)

    return ds, ds_time




def get_all_ds_from_experiment(experiment):
    n_runs = experiment.last_counter

    ds = []
    ds_time = []
    for _run_id in range(n_runs):
        _ds, _ds_time = get_ds_from_experiment(experiment, _run_id)
        ds.append(_ds)
        ds_time.append(_ds_time)

    return ds, ds_time


def get_parameters_from_ds(ds):
    '''
    Args:
        - ds: qcodes dataset
    Returns: 
        - parameters
        - ind_par_names
        - dep_par_names
    '''
    ### Fetching parameters from dataset
    return ds.paramspecs # returns dictionary with all parameters as keys as ParamSpec as value

def get_parameter_dependencies(parameters):
    '''
    Args:
        - parameters:
    Returns: 
        - ind_par_names
        - dep_par_names
    '''
    ind_par_names = []
    dep_par_names = []
    # print(parameters)
    ## Sorting dependent and independent parameters
    for par in parameters:
        if not parameters[par].depends_on_: # or depends_on_, which gives a string not a list
            ind_par_names.append(par)
        else:
            dep_par_names.append(par)

    return ind_par_names, dep_par_names



def get_data_from_ds_for_param(ds,parameter_name):
    '''
    Use together with get_parameter_dependencies to clarify interdependencies in data_dict
    '''    
    data_dict = ds.get_parameter_data()[parameter_name]

    return data_dict



## get dependent parameters - only if belong to different instrument than setpoints

