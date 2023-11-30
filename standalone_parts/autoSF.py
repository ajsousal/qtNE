import argparse
import sys
from PyQt6 import QtWidgets
from functools import partial
from numpy import floor


def fix_ipython():
    from IPython import get_ipython

    ipython = get_ipython()
    if ipython is not None:
        # print('here')
        ipython.run_line_magic("gui","qt5")

fix_ipython()

from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)

class autoSF(QtWidgets.QMainWindow): #QtWidgets.QDialog):

    def __init__(self, instrument = None, parent = None): #, parent=None):
        
        super(autoSF, self).__init__(parent) #parent)

        # self.main=parent

        self.instrument = instrument
        self.instrument_dictionary = self.instrument.parameters #instr_dict# dictionary with native parameters of instrument

        self.verLayout = QtWidgets.QVBoxLayout()
        self.horLayout = QtWidgets.QHBoxLayout()
        # treesLayout.addWidget(self.meta_tabs)

        self.setWindowTitle(self.instrument.full_name)

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        # self.setLayout(self.verLayout)
        self.setGeometry(500, 660, 200, 300) # x y w h
        
        

        self.show() 

        self.create_gui()


    def create_gui(self):
        labels = {}
        self.line_edit = {}
        self.buttons_get = {}
        self.buttons_set = {}
        
        max_pars_per_col = 20
        n_pars = len(self.instrument_dictionary)
        n_cols = int(1 + floor(n_pars/max_pars_per_col))

        self.verLayout = []
        for i in range(n_cols):
            self.verLayout.append(QtWidgets.QVBoxLayout())

        ind_row = 0
        ind_col = 0
        _added_to_layout = 0
        ## add list of parameters to gui
        for key in self.instrument_dictionary:
            

            try:
                value = getattr(self.instrument,key).get()
            except:
                print('Could not get parameter: '+key)
                value = 'NaN'
            
            
            # print(value)
            
            lineLayout = QtWidgets.QHBoxLayout()
            
            labels[key] = QtWidgets.QLabel(key)
            self.line_edit[key] = QtWidgets.QLineEdit()
            
            self.line_edit[key].setText(str(value)) #getattr(self.main.main.station.components[self.instrument_name],key)))

            lineLayout.addWidget(labels[key])
            lineLayout.addWidget(self.line_edit[key])

            self.buttons_get[key] = QtWidgets.QPushButton()
            self.buttons_get[key].setText('Get')
            # print(key)
            self.buttons_get[key].clicked.connect(partial(self._get_parameter, key=key)) #lambda getkey = key: self._get_parameter(getkey))

            lineLayout.addWidget(self.buttons_get[key])

            if getattr(self.instrument,key).settable: # parameter has set
                self.buttons_set[key] = QtWidgets.QPushButton()
                self.buttons_set[key].setText('Set')
                self.buttons_set[key].clicked.connect(partial(self._set_parameter, key=key)) #setkey= key, setval=self.line_edit[key].text(): self._set_parameter(setkey,setval))

                lineLayout.addWidget(self.buttons_set[key])

            else:
                pass
            
            # print(lineLayout)
            self.verLayout[ind_col].addItem(lineLayout)
            if ind_row > max_pars_per_col:
                self.horLayout.addItem(self.verLayout[ind_col])
                _added_to_layout = 1
                ind_col+=1
                ind_row = 0

            ind_row+=1
        
        if _added_to_layout == 0:
            self.horLayout.addItem(self.verLayout[ind_col])

        self.widget.setLayout(self.horLayout)


    def _get_parameter(self,key):
        '''
        '''
        print(self.instrument)
        print(key)
        value = getattr(self.instrument, key).get()
        self.line_edit[key].setText(str(value))
        # print()


    def _set_parameter(self,key):
        '''
        '''

        print('here '+key)
        value = float(self.line_edit[key].text())
        print(value)
        
        # print()
        getattr(self.instrument,key).set(value)
        self._get_parameter(key)

        # print()


if __name__ == '__main__':
    import sys
    
    # def start_threads(worker):

    
    if len(sys.argv) < 2:
        sys.argv += ['-d', os.path.join(os.path.expanduser('~'),
                                        'tmp', 'qdata')]

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--instrument', default=None, help="qcodes instrument initialized in Station")
    args = parser.parse_args()
    instrument = args.instrument

    def fix_ipython():
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is not None:
            # print('here')
            ipython.run_line_magic("gui","qt5")

    fix_ipython()
    
    # app = pg.mkQApp()
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # debugpy.debug_this_thread()

    autoSF = autoSF(instrument=instrument)
    
    # autoSF.show()
    # app.exec_()
    # sys.exit(app.exec())  

