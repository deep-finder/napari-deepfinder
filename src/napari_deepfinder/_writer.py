from __future__ import annotations
import napari.layers
import pandas as pd
from lxml import etree
import re


def write_annotations_xml(path: str, data: list):
    layers_df_list = []
    order = check_layer_order(data)
    for layer in data:
        layer_df = points_layer_to_df(layer[0])
        layers_df_list.append(layer_df)
    # reorder layers_df_list according to order
    sorted_layers_df_list = sort_df_list(layers_df_list, order)
    # transform to final dataframe and write
    final_df = layers_df_list_to_final_df(sorted_layers_df_list)
    if path[-4:] == '.xml':
        write_xml(final_df, path)
        return path
    else:
        write_xml(final_df, path + ".xml")
        return path + ".xml"


def sort_df_list(layers_df_list: list, order: list):
    new_list = []
    for i in order:
        new_list.append(layers_df_list[i - 1])
    return new_list


def check_layer_order(data: list):
    order = []
    for layer in data:
        name = layer[1]['name']
        regex = re.search("(\d+)$", name)
        if regex is not None:
            number_str = regex.group(0)
            number = int(number_str)
            order.append(number)
        else:
            raise ValueError('Layer must end with _classLabel')
    order_copy = order.copy()
    order_copy.sort()
    if [*range(1, len(order) + 1)] != order_copy:
        raise ValueError('Class labels must range from 1 to nb of classes')
    else:
        return order


def points_layer_to_df(layer: napari.layers.Layer):
    layer_df = pd.DataFrame(layer, columns=['x', 'y', 'z'])
    return layer_df


def layers_df_list_to_final_df(layers_df_list: list):
    final_list = []
    for i, dataframe in enumerate(layers_df_list):
        # there seems to be a bug in Napari, where a duplicated layer might be the ~same df object
        df = dataframe.copy(deep=True)
        class_label = i + 1
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
