import qcodes


def dictionary_to_dataset(data_dictionary):
    """ Convert dictionary to DataSet.

    Args:
        data_dictionary (dict): data to convert

    Returns:
        DataSet: converted data.
    """
    dataset = qcodes.new_data()
    dataset.metadata.update(data_dictionary['metadata'])

    for array_key, array_dict in data_dictionary['arrays'].items():
        data_array = _dictionary_to_data_array(array_dict)
        dataset.add_array(data_array)

    for array_key, array_dict in data_dictionary['arrays'].items():
        set_arrays_names = array_dict['set_arrays']
        set_arrays = tuple([dataset.arrays[name] for name in set_arrays_names])
        dataset.arrays[array_key].set_arrays = set_arrays

    return dataset


def dataset_to_dictionary(data_set, include_data=True, include_metadata=True):
    """ Convert DataSet to dictionary.

    Args:
        data_set (DataSet): The data to convert.
        include_data (bool): If True then include the ndarray field.
        include_metadata (bool): If True then include the metadata.

    Returns:
        dict: dictionary containing the serialized data.
    """
    data_dictionary = {'extra': {}, 'metadata': None, 'arrays': {}}

    for array_id, data_array in data_set.arrays.items():
        data_dictionary['arrays'][array_id] = _data_array_to_dictionary(data_array, include_data)

    data_dictionary['extra']['location'] = data_set.location
    if include_metadata:
        data_dictionary['metadata'] = data_set.metadata

    return data_dictionary



def _data_array_to_dictionary(data_array, include_data=True):
    """ Convert DataArray to a dictionary.

    Args:
        data_array (DataArray): The data to convert.
        include_data (bool): If True then include the ndarray field.

    Returns:
        dict: A dictionary containing the serialized data.
    """
    keys = ['label', 'name', 'unit', 'is_setpoint', 'full_name', 'array_id', 'shape']
    if include_data:
        keys.append('ndarray')

    data_dictionary = {key: getattr(data_array, key) for key in keys}
    data_dictionary['set_arrays'] = tuple(array.array_id for array in data_array.set_arrays)

    return data_dictionary


def _dictionary_to_data_array(array_dictionary):
    preset_data = array_dictionary['ndarray']
    array_id = array_dictionary.get('array_id', array_dictionary['name'])
    array_name = array_dictionary['name']
    if array_name is None:
        array_name = array_id
    array_full_name = array_dictionary['full_name']
    if array_full_name is None:
        array_full_name = array_name
    try:
        data_array = qcodes.DataArray(name=array_name,
                                    full_name=array_dictionary['full_name'],
                                    label=array_dictionary['label'],
                                    unit=array_dictionary['unit'],
                                    is_setpoint=array_dictionary['is_setpoint'],
                                    shape=tuple(array_dictionary['shape']),
                                    array_id=array_id,
                                    preset_data=preset_data)
    except:
        data_array = data_array.DataArray(name=array_name,
                                full_name=array_dictionary['full_name'],
                                label=array_dictionary['label'],
                                unit=array_dictionary['unit'],
                                is_setpoint=array_dictionary['is_setpoint'],
                                shape=tuple(array_dictionary['shape']),
                                array_id=array_id,
                                preset_data=preset_data)
    return data_array
