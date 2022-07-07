from __future__ import annotations
import napari.layers
import numpy
import pandas as pd
from lxml import etree
import re
import numpy as np
from deepfinder.utils import common as cm


def write_annotations_xml(path: str, data: list):
    """Writer for annotations in for of a xml object list"""
    layers_df_list = []
    class_numbers = []
    for layer in data:
        layer_df = points_layer_to_df(layer[0])
        layers_df_list.append(layer_df)
        class_number = layer_order(layer)
        class_numbers.append(class_number)
    sorted_layer_list, sorted_class_numbers = sort_layers(layers_df_list, class_numbers)
    final_df = layers_df_list_to_final_df(sorted_layer_list, sorted_class_numbers)
    if path[-4:] == '.xml':
        write_xml(final_df, path)
        return path
    else:
        path += '.xml'
        write_xml(final_df, path)
        return path


def write_labelmap(path: str, data: numpy.array, meta: dict):
    """Writer for labelmaps (segmentation maps)"""
    array_label = np.transpose(data, (2, 1, 0))
    type_list = ['int8', 'int16', 'uint8', 'uint16']
    # If the labelmap array is not in a correct type, cast to int8
    if array_label.dtype not in type_list:
        array_label = array_label.astype('int8')
    if path[-4:] == '.mrc':
        cm.write_array(array_label, path)
        return path
    else:
        path += '.mrc'
        cm.write_array(array_label, path)
        return path


def write_tomogram(path: str, data: numpy.array, meta: dict):
    """Writer for tomograms"""
    array_tomo = np.transpose(data, (2, 1, 0))
    if path[-4:] == '.mrc':
        cm.write_array(array_tomo, path)
        return path
    else:
        path += '.mrc'
        cm.write_array(array_tomo, path)
        return path


def layer_order(layer):
    name = layer[1]['name']
    regex = re.search("(\d+)$", name)
    if regex is not None:
        number_str = regex.group(0)
        number = int(number_str)
        return number
    else:
        raise ValueError('Layer must end with _classLabel')


def sort_layers(layers_df_list: list, class_numbers: list):
    sorted_layer_list = []
    index_list = [*range(len(class_numbers))]
    zipped = zip(index_list, class_numbers)
    sorted_zip = sorted(zipped, key=lambda x: x[1])
    sorted_index = [x[0] for x in sorted_zip]
    sorted_class_numbers = [x[1] for x in sorted_zip]
    for i in sorted_index:
        sorted_layer_list.append(layers_df_list[i])
    return sorted_layer_list, sorted_class_numbers


def points_layer_to_df(layer: napari.layers.Layer):
    layer_df = pd.DataFrame(layer, columns=['x', 'y', 'z'])
    return layer_df


def layers_df_list_to_final_df(layers_df_list: list, class_numbers: list):
    final_list = []
    for i, dataframe in enumerate(layers_df_list):
        # there seems to be a bug in Napari, where a duplicated layer might be the ~same df object
        df = dataframe.copy(deep=True)
        class_label = class_numbers[i]
        df.insert(loc=0, column='tomo_idx', value='')
        df.insert(loc=1, column='class_label', value=class_label)
        final_list.append(df)
    return pd.concat(final_list, ignore_index=True)


def write_xml(df: pd.DataFrame, filename: str):
    objl_xml = etree.Element('objlist')
    for idx in df.index:
        tidx = df.loc[idx, 'tomo_idx']
        lbl = df.loc[idx, 'class_label']
        x = df.loc[idx, 'x']
        y = df.loc[idx, 'y']
        z = df.loc[idx, 'z']
        obj = etree.SubElement(objl_xml, 'object')
        if tidx is not None:
            obj.set('tomo_idx', str(tidx))
        obj.set('class_label', str(lbl))
        obj.set('x', '%i' % x)
        obj.set('y', '%i' % y)
        obj.set('z', '%i' % z)
    tree = etree.ElementTree(objl_xml)
    tree.write(filename, pretty_print=True)
