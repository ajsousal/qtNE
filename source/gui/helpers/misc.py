import qcodes
# from . import json_serializer # commented on 31/05/2023
# from . import data_set, data_array
from qcodes.data import data_set, data_array
from . import data_set_conversions

import re
import os
import logging

import cv2

import copy
from collections import OrderedDict
import dateutil
import sys
import os
import numpy as np
import pprint
import matplotlib
import uuid
import qcodes
import warnings
import functools
import pickle
import inspect
import tempfile
from itertools import chain
import scipy.ndimage as ndimage
from functools import wraps
import datetime
import time
import importlib
import platform
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from qcodes.data.data_set import DataSet

try:
    from dulwich.repo import Repo, NotGitRepository
    from dulwich import porcelain
except ModuleNotFoundError:
    warnings.warn(
        'please install dulwich: pip install dulwich --global-option="--pure"')
    NotGitRepository = Exception

# explicit import
from qcodes.plots.qcmatplotlib import MatPlot

try:
    from qcodes.plots.pyqtgraph import QtPlot
except BaseException:
    pass

from qcodes.data.data_array import DataArray


try:
    import qtpy.QtGui as QtGui
    import qtpy.QtCore as QtCore
    import qtpy.QtWidgets as QtWidgets
except BaseException:
    pass


def findfilesR(p, patt, show_progress=False):
    """ Get a list of files (recursive)

    Args:

        p (string): directory
        patt (string): pattern to match
        show_progress (bool)
    Returns:
        lst (list of str)
    """
    lst = []
    rr = re.compile(patt)
    progress = {}
    for root, dirs, files in os.walk(p, topdown=True):
        frac = _walk_calc_progress(progress, root, dirs)
        if show_progress:
            tprint('findfilesR: %s: %.1f%%' % (p, 100 * frac))
        lst += [os.path.join(root, f) for f in files if re.match(rr, f)]
    return lst


def load_dataset(location, io=None, verbose=0):
    """ Load a dataset from storage

    An attempt is made to automatically detect the formatter. Supported are currently qcodes GNUPlotFormat,
    qcodes HDF5Format and json format.

    Args:
        location (str): either the relative or full location
        io (None or qcodes.DiskIO):
    Returns:
        dataset (DataSet or None)
    """

    if io is None:
        try:
            io = qcodes.DataSet.default_io
        except:
            io = data_set.DataSet.default_io
    try:
        formatters = [qcodes.DataSet.default_formatter]
    except:
        formatters = [data_set.DataSet.default_formatter]

    from qcodes.data.hdf5_format import HDF5FormatMetadata
    from qcodes.data.hdf5_format_hickle import HDF5FormatHickle
    formatters += [HDF5FormatHickle(), HDF5FormatMetadata()]

    from qcodes.data.hdf5_format import HDF5Format
    formatters += [HDF5Format()]

    from qcodes.data.gnuplot_format import GNUPlotFormat
    formatters += [GNUPlotFormat()]

    data = None

    if location.endswith('.json'):
        dataset_dictionary = json_serializer.load_json(location)
        data = data_set_conversions.dictionary_to_dataset(dataset_dictionary)
    else:
        # assume we have a QCoDeS dataset
        for ii, hformatter in enumerate(formatters):
            try:
                if verbose:
                    print('%d: %s' % (ii, hformatter))
                # data = qcodes.load_data(location, formatter=hformatter, io=io)
                data = data_set.load_data(
                    location, formatter=hformatter, io=io)
                if len(data.arrays) == 0:
                    data = None
                    raise Exception(
                        'empty dataset, probably a HDF5 format misread by GNUPlotFormat')
                logging.debug('load_data: loaded %s with %s' %
                              (location, hformatter))
            except Exception as ex:
                logging.info('load_data: location %s: failed for formatter %d: %s' % (
                    location, ii, hformatter))
                if verbose:
                    print(ex)
            finally:
                if data is not None:
                    if isinstance(hformatter, GNUPlotFormat):
                        # workaround for bug in GNUPlotFormat not saving the units
                        if '__dataset_metadata' in data.metadata:
                            dataset_meta = data.metadata['__dataset_metadata']
                            for key, array_metadata in dataset_meta['arrays'].items():
                                if key in data.arrays:
                                    if data.arrays[key].unit is None:
                                        if verbose:
                                            print(
                                                'load_dataset: updating unit for %s' % key)
                                        data.arrays[key].unit = array_metadata['unit']

                    if verbose:
                        print('success with formatter %s' % hformatter)
                    break
    if verbose:
        if data is None:
            print('could not load data from %s, returning None' % location)
    return data


# def dictionary_to_dataset(data_dictionary):
    # """ Convert dictionary to DataSet.

    # Args:
    # data_dictionary (dict): data to convert

    # Returns:
    # DataSet: converted data.
    # """
    # dataset = qcodes.new_data()
    # dataset.metadata.update(data_dictionary['metadata'])

    # for array_key, array_dict in data_dictionary['arrays'].items():
    # data_array = _dictionary_to_data_array(array_dict)
    # dataset.add_array(data_array)

    # for array_key, array_dict in data_dictionary['arrays'].items():
    # set_arrays_names = array_dict['set_arrays']
    # set_arrays = tuple([dataset.arrays[name] for name in set_arrays_names])
    # dataset.arrays[array_key].set_arrays = set_arrays

    # return dataset


# def dataset_to_dictionary(data_set, include_data=True, include_metadata=True):
    # """ Convert DataSet to dictionary.

    # Args:
    # data_set (DataSet): The data to convert.
    # include_data (bool): If True then include the ndarray field.
    # include_metadata (bool): If True then include the metadata.

    # Returns:
    # dict: dictionary containing the serialized data.
    # """
    # data_dictionary = {'extra': {}, 'metadata': None, 'arrays': {}}

    # for array_id, data_array in data_set.arrays.items():
    # data_dictionary['arrays'][array_id] = _data_array_to_dictionary(data_array, include_data)

    # data_dictionary['extra']['location'] = data_set.location
    # if include_metadata:
    # data_dictionary['metadata'] = data_set.metadata

    # return data_dictionary


# def _data_array_to_dictionary(data_array, include_data=True):
    # """ Convert DataArray to a dictionary.

    # Args:
    # data_array (DataArray): The data to convert.
    # include_data (bool): If True then include the ndarray field.

    # Returns:
    # dict: A dictionary containing the serialized data.
    # """
    # keys = ['label', 'name', 'unit', 'is_setpoint', 'full_name', 'array_id', 'shape']
    # if include_data:
    # keys.append('ndarray')

    # data_dictionary = {key: getattr(data_array, key) for key in keys}
    # data_dictionary['set_arrays'] = tuple(array.array_id for array in data_array.set_arrays)

    # return data_dictionary


# def _dictionary_to_data_array(array_dictionary):
    # preset_data = array_dictionary['ndarray']
    # array_id = array_dictionary.get('array_id', array_dictionary['name'])
    # array_name = array_dictionary['name']
    # if array_name is None:
    # array_name = array_id
    # array_full_name = array_dictionary['full_name']
    # if array_full_name is None:
    # array_full_name = array_name
    # try:
    # data_array = qcodes.DataArray(name=array_name,
    # full_name=array_dictionary['full_name'],
    # label=array_dictionary['label'],
    # unit=array_dictionary['unit'],
    # is_setpoint=array_dictionary['is_setpoint'],
    # shape=tuple(array_dictionary['shape']),
    # array_id=array_id,
    # preset_data=preset_data)
    # except:
    # data_array = data_array.DataArray(name=array_name,
    # full_name=array_dictionary['full_name'],
    # label=array_dictionary['label'],
    # unit=array_dictionary['unit'],
    # is_setpoint=array_dictionary['is_setpoint'],
    # shape=tuple(array_dictionary['shape']),
    # array_id=array_id,
    # preset_data=preset_data)
    # return data_array


def _walk_calc_progress(progress, root, dirs):
    """ Helper function """
    prog_start, prog_end, prog_slice = 0.0, 1.0, 1.0

    current_progress = 0.0
    parent_path, current_name = os.path.split(root)
    data = progress.get(parent_path)
    if data:
        prog_start, prog_end, subdirs = data
        i = subdirs.index(current_name)
        prog_slice = (prog_end - prog_start) / len(subdirs)
        current_progress = prog_slice * i + prog_start

        if i == (len(subdirs) - 1):
            del progress[parent_path]

    if dirs:
        progress[root] = (current_progress,
                          current_progress + prog_slice, dirs)

    return current_progress


def static_var(varname, value):
    """ Helper function to create a static variable

    Args:
        varname (str)
        value (anything)
    """
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate


@static_var("time", {'default': 0})
def tprint(string, dt=1, output=False, tag='default'):
    """ Print progress of a loop every dt seconds

    Args:
        string (str): text to print
        dt (float): delta time in seconds
        output (bool): if True return whether output was printed or not
        tag (str): optional tag for time
    Returns:
        output (bool)

    """
    if (time.time() - tprint.time.get(tag, 0)) > dt:
        print(string)
        tprint.time[tag] = time.time()
        if output:
            return True
        else:
            return
    else:
        if output:
            return False
        else:
            return


#######

def _convert_rgb_color_to_integer(rgb_color):
    if not isinstance(rgb_color, tuple) or not all(isinstance(i, int) for i in rgb_color):
        raise ValueError('Color should be an RGB integer tuple.')

    if len(rgb_color) != 3:
        raise ValueError(
            'Color should be an RGB integer tuple with three items.')

    if any(i < 0 or i > 255 for i in rgb_color):
        raise ValueError('Color should be an RGB tuple in the range 0 to 255.')

    red = rgb_color[0]
    green = rgb_color[1] << 8
    blue = rgb_color[2] << 16
    return int(red + green + blue)


def _convert_integer_to_rgb_color(integer_value):
    if integer_value < 0 or integer_value > 256 ** 3:
        raise ValueError('Integer value cannot be converted to RGB!')

    red = integer_value & 0xFF
    green = (integer_value >> 8) & 0xFF
    blue = (integer_value >> 16) & 0xFF
    return red, green, blue


# %% Copy mplimage to clipboard
try:
    _usegtk = 0
    try:
        import matplotlib.pyplot
        _usegtk = 0
    except BaseException:
        import pygtk
        pygtk.require('2.0')
        import gtk
        _usegtk = 1
        pass

    def mpl2clipboard(event=None, verbose=1, fig=None):
        """ Copy current Matplotlib figure to clipboard """
        if verbose:
            print('copy current Matplotlib figure to clipboard')
        if fig is None:
            fig = matplotlib.pyplot.gcf()
        else:
            print('mpl2clipboard: figure %s' % fig)
        w, h = fig.canvas.get_width_height()
        buf = np.fromstring(fig.canvas.tostring_argb(), dtype=np.uint8)
        buf.shape = (h, w, 4)
        im = np.roll(buf, 3, axis=2)
        im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)

        if _usegtk:
            r, tmpfile = tempfile.mkstemp(suffix='.png')
            cv2.imwrite(tmpfile, im)
            image = gtk.gdk.pixbuf_new_from_file(tmpfile)
            clipboard = gtk.clipboard_get()
            clipboard.set_image(image)
            clipboard.store()
        else:
            cb = QtWidgets.QApplication.clipboard()
            r, tmpfile = tempfile.mkstemp(suffix='.bmp')
            cv2.imwrite(tmpfile, im)
            qim = QtGui.QPixmap(tmpfile)
            cb.setPixmap(qim)

except BaseException:
    def mpl2clipboard(event=None, verbose=1, fig=None):
        """ Copy current Matplotlib figure to clipboard

        Dummy implementation
        """
        if verbose:
            print('copy current Matplotlib figure to clipboard not available')

    pass


@static_var('monitorindex', -1)
def tilefigs(lst, geometry=[2, 2], ww=None, raisewindows=False, tofront=False,
             verbose=0, monitorindex=None):
    """ Tile figure windows on a specified area

    Arguments
    ---------
        lst : list
                list of figure handles or integers
        geometry : 2x1 array
                layout of windows
        monitorindex (None or int): index of monitor to use for output
        ww (None or list): monitor sizes

    """
    mngr = plt.get_current_fig_manager()
    be = matplotlib.get_backend()
    if monitorindex is None:
        monitorindex = tilefigs.monitorindex

    if ww is None:
        ww = monitorSizes()[monitorindex]

    w = ww[2] / geometry[0]
    h = ww[3] / geometry[1]

    # wm=plt.get_current_fig_manager()

    if isinstance(lst, int):
        lst = [lst]
    if isinstance(lst, np.ndarray):
        lst = lst.flatten().astype(int)

    if verbose:
        print('tilefigs: ww %s, w %d h %d' % (str(ww), w, h))
    for ii, f in enumerate(lst):
        if isinstance(f, matplotlib.figure.Figure):
            fignum = f.number
        elif isinstance(f, (int, np.int32, np.int64)):
            fignum = f
        else:
            # try
            try:
                fignum = f.fig.number
            except BaseException:
                fignum = -1
        if not plt.fignum_exists(fignum):
            if verbose >= 2:
                print('tilefigs: f %s fignum: %s' % (f, str(fignum)))
            continue
        fig = plt.figure(fignum)
        iim = ii % np.prod(geometry)
        ix = iim % geometry[0]
        iy = np.floor(float(iim) / geometry[0])
        x = ww[0] + ix * w
        y = ww[1] + iy * h
        if verbose:
            print('ii %d: %d %d: f %d: %d %d %d %d' %
                  (ii, ix, iy, fignum, x, y, w, h))
            if verbose >= 2:
                print('  window %s' % mngr.get_window_title())
        if be == 'WXAgg':
            fig.canvas.manager.window.SetPosition((x, y))
            fig.canvas.manager.window.SetSize((w, h))
        if be == 'WX':
            fig.canvas.manager.window.SetPosition((x, y))
            fig.canvas.manager.window.SetSize((w, h))
        if be == 'agg':
            fig.canvas.manager.window.SetPosition((x, y))
            fig.canvas.manager.window.resize(w, h)
        if be == 'Qt4Agg' or be == 'QT4' or be == 'QT5Agg' or be == 'Qt5Agg':
            # assume Qt canvas
            try:
                fig.canvas.manager.window.move(x, y)
                fig.canvas.manager.window.resize(w, h)
                fig.canvas.manager.window.setGeometry(x, y, w, h)
                # mngr.window.setGeometry(x,y,w,h)
            except Exception as e:
                print('problem with window manager: ', )
                print(be)
                print(e)
                pass
        if raisewindows:
            mngr.window.raise_()
        if tofront:
            plt.figure(f)


def mkdirc(d):
    """ Similar to mkdir, but no warnings if the directory already exists """
    try:
        os.mkdir(d)
    except BaseException:
        pass
    return d


# from qtt.utilities.tools

def reshape_metadata(dataset, printformat='dict', add_scanjob=True, add_gates=True, add_analysis_results=True, verbose=0):
    """ Reshape the metadata of a DataSet.

    Args:
        dataset (DataSet or qcodes.Station): a dataset of which the metadata will be reshaped.
        printformat (str): can be 'dict' or 'txt','fancy' (text format).
        add_scanjob (bool): If True, then add the scanjob at the beginning of the notes.
        add_analysis_results (bool): If True, then add the analysis_results at the beginning of the notes.
        add_gates (bool): If True, then add the scanjob at the beginning of the notes.
        verbose (int): verbosity (0 == silent).

    Returns:
        str: the reshaped metadata.

    """
    if isinstance(dataset, qcodes.Station):
        station = dataset
        all_md = station.snapshot(update=False)['instruments']
        header = None
    else:
        tmp = dataset.metadata.get('station', None)
        if tmp is None:
            all_md = {}
        else:
            all_md = tmp['instruments']

        header = 'dataset: %s' % dataset.location

        if hasattr(dataset.io, 'base_location'):
            header += ' (base %s)' % dataset.io.base_location

    if add_gates:
        gate_values = dataset.metadata.get('allgatevalues', None)

        if gate_values is not None:
            gate_values = dict([(key, np.around(value, 3))
                                for key, value in gate_values.items()])
            header += '\ngates: ' + str(gate_values) + '\n'

    scanjob = dataset.metadata.get('scanjob', None)
    if scanjob is not None and add_scanjob:
        s = pprint.pformat(scanjob)
        header += '\n\nscanjob: ' + str(s) + '\n'

    analysis_results = dataset.metadata.get('analysis_results', None)
    if analysis_results is not None and add_analysis_results:
        s = pprint.pformat(analysis_results)
        header += '\n\analysis_results: ' + str(s) + '\n'

    metadata = OrderedDict()
    # make sure the gates instrument is in front
    all_md_keys = sorted(sorted(all_md), key=lambda x: x ==
                         'gates', reverse=True)
    for x in all_md_keys:
        metadata[x] = OrderedDict()
        if 'IDN' in all_md[x]['parameters']:
            metadata[x]['IDN'] = dict({'name': 'IDN', 'value': all_md[
                x]['parameters']['IDN']['value']})
            metadata[x]['IDN']['unit'] = ''
        for y in sorted(all_md[x]['parameters'].keys()):
            try:
                if y != 'IDN':
                    metadata[x][y] = OrderedDict()
                    param_md = all_md[x]['parameters'][y]
                    metadata[x][y]['name'] = y
                    if isinstance(param_md['value'], (float, np.float64)):
                        metadata[x][y]['value'] = float(
                            format(param_md['value'], '.3f'))
                    else:
                        metadata[x][y]['value'] = str(param_md['value'])
                    metadata[x][y]['unit'] = param_md.get('unit', None)
                    metadata[x][y]['label'] = param_md.get('label', None)
            except KeyError as ex:
                if verbose:
                    print('failed on parameter %s / %s: %s' % (x, y, str(ex)))

    if printformat == 'dict':
        ss = str(metadata).replace('(', '').replace(
            ')', '').replace('OrderedDict', '')
    else:  # 'txt' or 'fancy'
        ss = ''
        for k in metadata:
            if verbose:
                print('--- %s' % k)
            s = metadata[k]
            ss += '\n## %s:\n' % k
            for p in s:
                pp = s[p]
                if verbose:
                    print('  --- %s: %s' % (p, pp.get('value', '??')))
                ss += '%s: %s (%s)' % (pp['name'],
                                       pp.get('value', '?'), pp.get('unit', ''))
                ss += '\n'

    if header is not None:
        ss = header + '\n\n' + ss
    return ss


try:
    import qtpy.QtGui as QtGui
    import qtpy.QtWidgets as QtWidgets

    def monitorSizes(verbose=0):
        """ Return monitor sizes."""
        _qd = QtWidgets.QDesktopWidget()
        if sys.platform == 'win32' and _qd is None:
            import ctypes
            user32 = ctypes.windll.user32
            wa = [
                [0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]]
        else:
            _applocalqt = QtWidgets.QApplication.instance()

            if _applocalqt is None:
                _applocalqt = QtWidgets.QApplication([])
                _qd = QtWidgets.QDesktopWidget()
            else:
                _qd = QtWidgets.QDesktopWidget()

            nmon = _qd.screenCount()
            wa = [_qd.screenGeometry(ii) for ii in range(nmon)]
            wa = [[w.x(), w.y(), w.width(), w.height()] for w in wa]

            if verbose:
                for ii, w in enumerate(wa):
                    print('monitor %d: %s' % (ii, str(w)))

        return wa
except BaseException:
    def monitorSizes(verbose=0):
        """ Dummy function for monitor sizes."""
        return [[0, 0, 1600, 1200]]
    pass


def diffImage(im, dy, size=None):
    """ Simple differentiation of an image.

    Args:
        im (numpy array): input image.
        dy (integer or string): method of differentiation. For an integer it is the axis of differentiation.
            Allowed strings are 'x', 'y', 'xy'.
        size (str): describes the size e.g. 'same'.

    """
    if dy == 0 or dy == 'x':
        im = np.diff(im, n=1, axis=1)
        if size == 'same':
            im = np.hstack((im, im[:, -1:]))
    elif dy == 1 or dy == 'y':
        im = np.diff(im, n=1, axis=0)
        if size == 'same':
            im = np.vstack((im, im[-1:, :]))
    elif dy == -1:
        im = -np.diff(im, n=1, axis=0)
        if size == 'same':
            im = np.vstack((im, im[-1:, :]))
    elif dy == 2 or dy == 'xy':
        imx = np.diff(im, n=1, axis=1)
        imy = np.diff(im, n=1, axis=0)
        im = imx[0:-1, :] + imy[:, 0:-1]
    elif dy is None:
        pass
    else:
        raise Exception('differentiation method %s not supported' % dy)
    return im
