from qcodes.tests.instrument_mocks import DummyInstrument, DummyAttrInstrument
from qcodes_contrib_drivers.drivers.Keysight.SD_common.SD_DIG import SD_DIG

from qcodes.instrument.base import Instrument


class Dummy(DummyAttrInstrument):

    def __init__(self, name, **kwargs):
        
        super().__init__(name)

        self.stuff1 = kwargs['stuff_1']

        print('printing stuff_1')
        print(self.stuff1)

        self.ch1.set(10)
        print(self.ch1.get())





