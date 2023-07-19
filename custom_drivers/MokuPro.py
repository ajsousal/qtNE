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
        
        

