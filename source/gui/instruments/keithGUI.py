# %% Load packages

import argparse
import logging
import os

import pyqtgraph as pg
import qtpy.QtGui as QtGui
import qtpy.QtWidgets as QtWidgets
from qtpy.QtWidgets import QFileDialog, QWidget

import qcodes
from qcodes.plots.pyqtgraph import QtPlot




# %% Main class


class KeithGUI(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        """ Contstructs a simple viewer for Qcodes data.

        Args:
            data_directory (string or None): The directory to scan for experiments.
            default_parameter (string): A name of default parameter to plot.
            extensions (list): A list with the data file extensions to filter.
            verbose (int): The logging verbosity level.
        """
        super(KeithGUI, self).__init__(parent)


        self.main=parent