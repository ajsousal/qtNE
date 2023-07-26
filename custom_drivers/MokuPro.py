import sys
import numpy as np
from functools import partial
from time import perf_counter
from os import path
from qcodes import Instrument
from qcodes.utils.validators import Numbers

from moku.instruments import Oscilloscope

class MokuScope(Instrument):

    def __init__(self,name: str, IP_address: str, **kwargs):
    
        super().__init__(name,**kwargs)
        
        self.i = Oscilloscope(IP_address, force_connect=True)



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
        
        

