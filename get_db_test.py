import qcodes as qc
import os
import datetime

from source.tools import db_comms

_date_format_string = "%Y%m%d" 
_time_format_string = "%H%M%S"


_old_data_rule = True

data_dir = "C:\qtNE_dbs_2021\Antonio"


db_list = db_comms.get_databases(data_dir)

db = db_list[0]

exp_list, _ = db_comms.get_experiments_from_db(db)

exp = exp_list[0]

ds, ds_time = db_comms.get_ds_from_experiment(exp, 0)



