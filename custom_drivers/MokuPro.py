import sys
import numpy as np
from functools import partial
from time import perf_counter
from os import path
from qcodes import Instrument
from qcodes.utils.validators import Numbers

from moku.instruments import Oscilloscope

class MokuScope(Instrument):

    def __init__(self,name: str, address: str, **kwargs):
    
        super().__init__(name,**kwargs)
        
        self.i = Oscilloscope(address, force_connect=True)


    def get_idn(self):
        """
        Overwrites the get_idn function using constants as the hardware
        does not have a proper \*IDN function.
        """
        return -1

    def get_reading_buffer(self):
        
        path_to_save = 'C:\\_measurement_software\\qtNE\\tmp'
        fname_to_save = 'tmp_data.csv'#npy'

        response = self.i.save_high_res_buffer(comments='tmp')
        print(response)
        fname_memory = response["file_name"]
        self.i.download(target='ssd',file_name=fname_memory,local_path=path.join(path_to_save,fname_to_save))
        # self.i.delete(target='persist',file_name=fname_memory)
        data_raw = np.load(path.join(path_to_save,fname_to_save),allow_pickle=True)
        # print(data_raw)
        data_array = data_raw # [array(data_raw['time']), array(data_raw['ch'+dictionary['input_ch']])/dictionary['gain']]
        
        return data_raw
    
        

