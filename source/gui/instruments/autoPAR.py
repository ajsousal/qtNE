import sys
from PyQt6 import QtWidgets


class autoPAR(QtWidgets.QDialog):

    def __init__(self, instrument = None, instr_dict=None): #, parent=None):
                
        super(autoPAR, self).__init__() #parent)

        # self.main=parent

        self.instrument = instrument
        self.instrument_dictionary = instr_dict# dictionary with native parameters of instrument

        self.verLayout = QtWidgets.QVBoxLayout()
        # treesLayout.addWidget(self.meta_tabs)

        self.setWindowTitle('SoftPanel')

        # self.setLayout(self.verLayout)
        self.setGeometry(500, 660, 200, 300) # x y w h
        
        

        self.show() 
        
        self.create_gui()