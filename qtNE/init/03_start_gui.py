#----------------------%% GUI initialization
from qtpy.QtWidgets import QApplication
import os
import sys
from source.gui import stationGUI

with open(os.path.join(os.getcwd(),'qtNE.cfg'),'r') as cfg_file:
        cfgs=json.load(cfg_file)

def fix_ipython():
    from IPython import get_ipython

    ipython = get_ipython()
    if ipython is not None:
        # print('here')
        ipython.run_line_magic("gui","qt5")

fix_ipython()

app=QApplication(sys.argv)
stationgui=stationGUI.StationGUI(station=station,database_dir=cfgs['datadir'])

## uncomment this to run in debug mode (VSCode)
# app.exec_()
# sys.exit(app.exec_())
