import sys
from PyQt6 import QtWidgets


class autoSF(QtWidgets.QDialog):

    def __init__(self, instrument = None, instr_dict=None): #, parent=None):
                
        super(autoSF, self).__init__() #parent)

        # self.main=parent

        self.instrument = instrument
        self.instrument_dictionary = instr_dict# dictionary with native parameters of instrument

        self.verLayout = QtWidgets.QVBoxLayout()
        # treesLayout.addWidget(self.meta_tabs)

        self.setWindowTitle('SoftPanel')

        self.setLayout(self.verLayout)
        self.setGeometry(500, 660, 200, 300) # x y w h
        
        self.create_gui()

        self.show() 


    def create_gui(self):
        # app = QApplication(sys.argv)
        # window = QWidget()
        labels = {}
        self.line_edit = {}
        self.buttons_get = {}
        self.buttons_set = {}
        for key in self.instrument_dictionary:
            
            value = getattr(self.instrument,key)
            
            lineLayout = QtWidgets.QHBoxLayout()
            
            labels[key] = QtWidgets.QLabel(key)
            self.line_edit[key] = QtWidgets.QLineEdit()
            
            self.line_edit[key].setText(str(value)) #getattr(self.main.main.station.components[self.instrument_name],key)))

            lineLayout.addWidget(labels[key])
            lineLayout.addWidget(self.line_edit[key])

            self.buttons_get[key] = QtWidgets.QPushButton()
            self.buttons_get[key].setText('Get')
            self.buttons_get[key].clicked.connect(lambda getkey = key: self._get_parameter(getkey))

            lineLayout.addWidget(self.buttons_get[key])

            if getattr(self.instrument,key) is None: # parameter has set
                self.buttons_set[key] = QtWidgets.QPushButton()
                self.buttons_set[key].setText('Set')
                self.buttons_get[key].clicked.connect(lambda setkey= key, setval=line_edit[key].getText(): self._set_parameter(setkey,setval))

                lineLayout.addWidget(self.buttons_set[key])

            else:
                pass
            
            self.verLayout.addItem(lineLayout)



    def _get_parameter(self,key):
        '''
        '''
        value = getattr(self.instrument, key)
        self.line_edit[key].setText(str(value))
        # print()


    def _set_parameter(self,key,value):
        '''
        '''

        setattr(self.instrument,key,value)
        self._get_parameter(key)

        # print()


            

