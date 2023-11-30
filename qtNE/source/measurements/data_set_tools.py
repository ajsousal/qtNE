"""DataSet class and factory functions."""

import qcodes
import numpy as np

import pandas
import csv
import itertools

# from source.gui.helpers import data_set, data_array
from qcodes_loop.data import data_set, data_array


def correctarrays(data_set=[], combined_sweep=[], combined_step=[], array_sweep=[], array_step=[], fixed_dacs=[]):
    """
    Fixes the data to account for combined and/or fixed parameters
    FIX: not yet properly defined for 2D sweeps: use list as swept_array, condition to identify two setpoints
    """

    if not combined_sweep == []:  # is None:
        try:
            # is crazy hard to get to the actual data point array
            data_set.arrays[list(data_set.arrays)[0]].ndarray = array_sweep[0]

            data_set.arrays[list(data_set.arrays)[0]].action_indices = data_set.arrays['gates_' +
                                                                                       combined_sweep[0]].action_indices  # is crazy hard to get to the actual data point array
            data_set.arrays[list(data_set.arrays)[0]].full_name = data_set.arrays[list(
                data_set.arrays)[0]].name+'_set'  # is crazy hard to get to the actual data point array

        except:
            print('Error: Please define swept array for combined gates')
            return

        for i in range(len(combined_sweep)):
            data_set.arrays['gates_'+combined_sweep[i]].array_id = data_set.arrays['gates_' +
                                                                                   combined_sweep[i]].array_id+'_cbsweep'  # +'_combi'

            print(data_set)
            for kk in range(len(list(data_set.arrays))):
                # print(kk)
                print(data_set.arrays[list(
                    data_set.arrays)[kk]].action_indices)
                print(data_set.arrays[list(data_set.arrays)[kk]].full_name)
                print(data_set.arrays[list(data_set.arrays)[kk]].name)

    if not combined_step == []:  # is None:
        try:
            data_set.arrays[list(data_set.arrays)[1]].ndarray = np.tile(array_step[0], (len(data_set.arrays[list(
                data_set.arrays)[1]].ndarray), 1))  # is crazy hard to get to the actual data point array
            print(data_set.arrays[list(data_set.arrays)[1]].ndarray)
        except:
            print('Error: Please define step array for combined gates')
            return
        for i in range(len(combined_step)):
            data_set.arrays['gates_'+combined_step[i]].array_id = data_set.arrays['gates_' +
                                                                                  combined_step[i]].array_id+'_cbstep'  # +'_combi'

    if not fixed_dacs == []:  # is None:
        for i in range(len(fixed_dacs)):
            data_set.arrays['gates_'+fixed_dacs[i]
                            ].array_id = data_set.arrays['gates_'+fixed_dacs[i]].array_id+'_fix'

            for kk in data_set.arrays:
                print(kk)
                print(kk.action_indices)

            print(data_set.arrays['gates_'+fixed_dacs[i]].action_indices)


def remove_array_clean(data_set, array_id):
    """ Remove an array from a dataset

    Throws an exception when the array specified is refereced by other
    arrays in the dataset.

    Args:
        array_id (str): array_id of array to be removed
    """
    for a in data_set.arrays:
        sa = data_set.arrays[a].set_arrays
        if array_id in [a.array_id for a in sa]:
            raise Exception(
                'cannot remove array %s as it is referenced by a' % array_id)
    _ = data_set.arrays.pop(array_id)


def load_data_generic(filename):
    # print(filename)
    if filename.endswith('.hdf5'):
        print('not implemented yet')
        import h5py

        with h5py.File(filename, 'r') as f:
            print(f)
            print(f.keys())

    else:
        with open(filename, 'r') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read())

        with open(filename, 'r') as csvfile:
            readers = itertools.tee(csv.reader(
                csvfile, delimiter=dialect.delimiter), 4)

            iterable = (1 for row in readers[0])
            numrows = np.sum(np.fromiter(iterable, int))

            for row in itertools.islice(readers[1], numrows-1, numrows):
                numcols = np.shape(row)[0]

            indrow_data = 0
            for row in readers[2]:

                iterable = (isnumber(element) for element in row)
                numels_row = np.sum(np.fromiter(iterable, int))
                if numels_row == numcols:
                    break
                indrow_data += 1

            header_cols_row = -1
            indrow = 0
            for row in itertools.islice(readers[3], indrow_data):
                if np.shape(row)[0] == numcols:
                    header_cols_row = indrow
                    break
                indrow += 1

        if header_cols_row != -1:
            panda_kwargs = {'delimiter': dialect.delimiter,
                            'header': header_cols_row}

        else:
            header_cols = []
            for kk in range(numcols):
                header_cols.append('col_'+str(kk))

            panda_kwargs = {'delimiter': dialect.delimiter,
                            'header': 0,
                            'names': header_cols}

        dataraw = pandas.read_csv(filename, **panda_kwargs)
        try:
            _dataset = qcodes.data.data_set.new_data()
        except:
            _dataset = data_set.new_data()
        indrow = 0
        while True:
            if not isnumber(dataraw.iloc[indrow, 0]):
                dataraw = dataraw.iloc[indrow+1:]
            else:
                break
            indrow += 1

        dataraw = dataraw.astype('float')

    # 2D data
    if dataraw.iloc[indrow, 0] == dataraw.iloc[indrow+1, 0]:
        setp1_array = []
        indrow = 0
        while dataraw.iloc[indrow, 0] == dataraw.iloc[indrow+1, 0]:
            indrow += 1
        setp0_array = list(
            dataraw.iloc[range(indrow, len(dataraw.iloc[:, 0]), indrow), 0])

        colname = dataraw.columns[0]
        try:
            data_arr = qcodes.DataArray(name=colname,
                                        label=colname,
                                        unit='a.u.',
                                        array_id=colname,
                                        is_setpoint=True,
                                        preset_data=setp0_array,
                                        full_name=colname)
        except:
            data_arr = data_array.DataArray(name=colname,
                                            label=colname,
                                            unit='a.u.',
                                            array_id=colname,
                                            is_setpoint=True,
                                            preset_data=setp0_array,
                                            full_name=colname)
        _dataset.add_array(data_arr)

        for indset0 in range(0, len(setp0_array)):
            # print(str(indset0*indrow+indset0)+', '+str(indrow*(indset0+1)+indset0+1))
            try:
                setp1_array.append(list(
                    dataraw.iloc[range(indset0*indrow+indset0, indrow*(indset0+1)+indset0+1), 1]))
            except:
                setp1_array.append(list(dataraw.iloc[range(
                    indset0*indrow+indset0, np.shape(dataraw.iloc[:, 0])[0]), 1]))

        colname = dataraw.columns[1]
        try:
            data_arr = qcodes.DataArray(name=colname,
                                        label=colname,
                                        unit='a.u.',
                                        array_id=colname,
                                        is_setpoint=True,
                                        preset_data=setp1_array,
                                        full_name=colname)
        except:
            data_arr = data_array.DataArray(name=colname,
                                            label=colname,
                                            unit='a.u.',
                                            array_id=colname,
                                            is_setpoint=True,
                                            preset_data=setp1_array,
                                            full_name=colname)

        _dataset.add_array(data_arr)

        for indcol in range(2, len(dataraw.columns)):
            arr = []
            for indset0 in range(0, len(setp0_array)):
                try:
                    arr.append(list(dataraw.iloc[range(
                        indset0*indrow+indset0, indrow*(indset0+1)+indset0+1), indcol]))
                except:
                    arr.append(list(dataraw.iloc[range(
                        indset0*indrow+indset0, np.shape(dataraw.iloc[:, 0])[0]), indcol]))
            colname = dataraw.columns[indcol]
            try:
                data_arr = qcodes.DataArray(name=colname,
                                            label=colname,
                                            unit='a.u.',
                                            array_id=colname,
                                            is_setpoint=False,
                                            set_arrays=[
                                                getattr(_dataset, dataraw.columns[indd]) for indd in range(0, 2)],
                                            preset_data=arr,
                                            full_name=colname)
            except:
                data_arr = data_array.DataArray(name=colname,
                                                label=colname,
                                                unit='a.u.',
                                                array_id=colname,
                                                is_setpoint=False,
                                                set_arrays=[
                                                    getattr(_dataset, dataraw.columns[indd]) for indd in range(0, 2)],
                                                preset_data=arr,
                                                full_name=colname)
            _dataset.add_array(data_arr)

    # 1D data
    else:
        setp_array = dataraw.iloc[:, 0]

        for indcol in range(1, len(dataraw.columns)):
            arr = list(dataraw.iloc[:, indcol])
            colname = dataraw.columns[indcol]
            try:
                data_arr = qcodes.DataArray(name=colname,
                                            label=colname,
                                            unit='a.u.',
                                            array_id=colname,
                                            is_setpoint=False,
                                            set_arrays=[
                                                getattr(_dataset, dataraw.columns[0])],
                                            preset_data=arr,
                                            full_name=colname)
            except:
                data_arr = data_array.DataArray(name=colname,
                                                label=colname,
                                                unit='a.u.',
                                                array_id=colname,
                                                is_setpoint=False,
                                                set_arrays=[
                                                    getattr(_dataset, dataraw.columns[0])],
                                                preset_data=arr,
                                                full_name=colname)

            _dataset.add_array(data_arr)

    return _dataset


def isnumber(str):
    try:
        float(str)
    except ValueError:
        return False
    return True
