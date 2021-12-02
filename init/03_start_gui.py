#----------------------%% GUI initialization
from qtpy.QtWidgets import QApplication
import sys

with open(os.path.join(os.getcwd(),'qtNE.cfg'),'r') as cfg_file:
        cfgs=json.load(cfg_file)


app=QApplication(sys.argv)
stationgui=stationGUI.StationGUI(station=station,database_dir=cfgs['datadir'])

## uncomment this to run in debug mode (VSCode)
#app.exec()