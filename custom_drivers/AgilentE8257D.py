from numpy import pi

from qcodes import VisaInstrument, validators as vals
from qcodes.utils.validators import numbertypes


class Agilent_E8257D(VisaInstrument):
    """
    This is the QCoDeS driver for the Agilent_E8527D signal generator.

    Status: beta-version.
        TODO:
        - Add all parameters that are in the manual

    This driver will most likely work for multiple Agilent sources.

    This driver does not contain all commands available for the E8527D but
    only the ones most commonly used.
    """
    def __init__(self, name: str, address: str,
                 step_attenuator: bool = False, **kwargs) -> None:
        super().__init__(name, address, **kwargs)

        self.add_parameter(name='frequency',
                           label='Frequency',
                           unit='Hz',
                           get_cmd='FREQ:CW?',
                           set_cmd='FREQ:CW' + ' {:.4f}',
                           get_parser=float,
                           set_parser=float,
                           vals=vals.Numbers(1e5, 50e9)) # edited for type 550 Unit (check manual)
        self.add_parameter(name='phase',
                           label='Phase',
                           unit='deg',
                           get_cmd='PHASE?',
                           set_cmd='PHASE' + ' {:.8f}',
                           get_parser=self.rad_to_deg,
                           set_parser=self.deg_to_rad,
                           vals=vals.Numbers(-180, 180))
        # min_power = -135 if step_attenuator else -20
        min_power= -110 # option 550

        self.add_parameter(name='power',
                           label='Power',
                           unit='dBm',
                           get_cmd='POW:AMPL?',
                           set_cmd='POW:AMPL' + ' {:.4f}',
                           get_parser=float,
                           set_parser=float,
                           vals=vals.Numbers(min_power, 16))
        self.add_parameter('status',
                           get_cmd=':OUTP?',
                           set_cmd='OUTP {}',
                           get_parser=self.parse_on_off,
                           # Only listed most common spellings ideally want a
                           # .upper val for Enum or string.
                           vals=vals.Enum('on', 'On', 'ON',
                                          'off', 'Off', 'OFF'))
                                          
        self.add_parameter('modulation',
                            get_cmd=':OUTP:MOD?',
                            set_cmd='OUTP:MOD {}',
                            vals=vals.Enum('on', 'On', 'ON',
                                          'off', 'Off', 'OFF'))
                                          
        self.add_parameter('pulse_mod_ext_polarity',
                            get_cmd='PULM:EXT:POL?',
                            set_cmd='PULM:EXT:POL {}',
                            vals=vals.Enum('normal','NORM','inverted','INV'))

        self.add_parameter('pulse_mod_delay',
                            get_cmd='PULM:INT:DEL?',
                            set_cmd='PULM:INT:DEL {}',
                            set_parser=float,
                            get_parser=float,
                            vals=vals.Numbers(70e-9,40))
                            
        self.add_parameter('pulse_mod_delay_step',
                            get_cmd='PULM:INT:DEL:STEP?',
                            set_cmd='PULM:INT:DEL:STEP {}',
                            set_parser=float,
                            get_parser=float)
        
        self.add_parameter('pulse_mod_frequency',
                            get_cmd='PULM:INT:FREQ?',
                            set_cmd='PULM:INT:FREQ {}',
                            set_parser=float,
                            get_parser=float,
                            vals=vals.Numbers(1,1e8))
        
        self.add_parameter('pulse_mod_frequency_step',
                            get_cmd='PULM:INT:FREQ:STEP?',
                            set_cmd='PULM:INT:FREQ:STEP {}',
                            set_parser=float,
                            get_parser=float)

        self.add_parameter('pulse_mod_period',
                            get_cmd='PULM:INT:PER?',
                            set_cmd='PULM:INT:PER {}',
                            set_parser=float,
                            get_parser=float,
                            vals=vals.Numbers(10e-9,1))

        self.add_parameter('pulse_mod_period_step',
                            get_cmd='PULM:INT:PER:STEP?',
                            set_cmd='PULM:INT:PER:STEP {}',
                            set_parser=float,
                            get_parser=float)

        self.add_parameter('pulse_mod_width',
                            get_cmd='PULM:INT:PWID?',
                            set_cmd='PULM:INT:PWID {}',
                            set_parser=float,
                            get_parser=float,
                            vals=vals.Numbers(20e-9,1e-6))

        self.add_parameter('pulse_mod_width_step',
                            get_cmd='PULM:INT:PWID:STEP?',
                            set_cmd='PULM:INT:PWID:STEP {}',
                            set_parser=float,
                            get_parser=float)
                            
        self.add_parameter('pulse_mod_trigger_type',
                            get_cmd='PULM:SOUR?',
                            set_cmd='PULM:SOUR {}')
                            
        self.add_parameter('pulse_mod_internal_trigger',
                            get_cmd='PULM:SOUR:INT?',
                            set_cmd='PULM:SOUR:INT {}')
                            
        # self.add_parameter('pulse_mod_status',
                           # get_cmd='PULM:SOUR:STAT?',
                           # set_cmd='PULM:SOUR:STAT {}',
                           # vals=vals.Enum('on', 'On', 'ON',
                                          # 'off', 'Off', 'OFF'))
                            


        self.connect_message()

    # Note it would be useful to have functions like this in some module instead
    # of repeated in every instrument driver.
    @staticmethod
    def rad_to_deg(angle_rad: numbertypes) -> float:
        angle_deg = float(angle_rad)/(2*pi)*360
        return angle_deg

    @staticmethod
    def deg_to_rad(angle_deg: numbertypes) -> float:
        angle_rad = float(angle_deg)/360 * 2 * pi
        return angle_rad

    @staticmethod
    def parse_on_off(stat: str) -> str:
        if stat.startswith('0'):
            stat = 'Off'
        elif stat.startswith('1'):
            stat = 'On'
        return stat

    def on(self):
        self.set('status', 'on')

    def off(self):
        self.set('status', 'off')
