import numpy as np
import pandas as pd
from pathlib import Path
from deepfinder.utils.common import read_array

# readable tomograms, see read_array function from deepfinder
extensions_tomo = ['.mrc', '.map', '.rec', '.h5', '.tif', '.TIF']
extensions_labels = ['.xml', '.ods', '.xls', '.xlsx']
extensions = extensions_tomo + extensions_labels


def napari_get_reader(path):
    """A basic implementation of a Reader contribution.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    # if isinstance(path, list):
    #     # reader plugins may be handed single path, or a list of paths.
    #     # if it is a list, it is assumed to be an image stack... -> image and labels for example!
    #     # so we are only going to look at the first file.
    #     path = path[0]
    if isinstance(path, list):
        for single_file in path:
            # if we know we cannot read the file, we immediately return None.
            if not single_file.endswith(tuple(extensions)):
                return None
        return reader_function
    else:
        # if we know we cannot read the file, we immediately return None.
        if not path.endswith(tuple(extensions)):
            return None
        # otherwise, we return the *function* that can read ``path``.
        return reader_function


def reader_function(path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of layer.
        Both "meta", and "layer_type" are optional. napari will default to
        layer_type=="image" if not provided
    """
    layer_data = []
    # handle both a string and a list of strings
    paths = [path] if isinstance(path, str) else path
    for _path in paths:
        if _path.endswith(tuple(extensions_tomo)):
            # load all files into array
            data = read_array(_path)
            # invert axes from z,y,x to x,y,z (weird convention)
            data = np.transpose(data, (2, 1, 0))
            # if the data is the target value, import as labels layer
            if data.dtype.name == 'int8':
                # unique_labels = np.unique(data)
                # optional kwargs for the corresponding viewer.add_* method
                add_kwargs = {}
                layer_type = "labels"  # optional, default is "image"
            else:
                # optional kwargs for the corresponding viewer.add_* method
                add_kwargs = {}
                layer_type = "image"  # optional, default is "image"
            layer_data.append((data, add_kwargs, layer_type))
        if _path.endswith(tuple(extensions_labels)):
            name = Path(_path).stem
            df = read_label(_path)
            unq_label = df['class_label'].unique()
            for i in range(len(unq_label)):
                df_label = df.loc[df['class_label'] == unq_label[i]]
                data = df_label[['x', 'y', 'z']].values
                size = 10  # this default value could be changed for each label
                color = 'white'  # this default value could be changed for each label
                name_id = name + '_' + str(unq_label[i])
                add_kwargs = {'out_of_slice_display': True,
                              'size': size,
                              'face_color': color,
                              'name': name_id}
                layer_type = "points"
                layer_data.append((data, add_kwargs, layer_type))
    return layer_data


def read_label(filename):
    if filename.endswith(".xml"):
        data = pd.read_xml(filename)
    # else: assuming the data is in ods, xls or xlsx format
    else:
        data = pd.read_xml(filename)
    return data
