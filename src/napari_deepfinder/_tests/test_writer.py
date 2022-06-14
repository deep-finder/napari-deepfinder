from napari_deepfinder import write_annotations_xml
import numpy as np
import os


def test_writing_one_layer(tmp_path):
    data = np.array([[0, 0, 0]])
    path = os.path.join(str(tmp_path), "test_labels")
    path_with_extension = os.path.join(str(tmp_path), "test_labels2.xml")
    write_annotations_xml(path, [(data, {'name': 'test_1'}, 'points')])
    write_annotations_xml(path_with_extension, [(data, {'name': 'test'}, 'points')])


def test_writing_multiple_layers(tmp_path):
    data = np.array([[0, 0, 0]])
    data_2 = np.array([[1, 1, 1], [0, 0, 0]])
    path = os.path.join(str(tmp_path), "test_labels")
    write_annotations_xml(path, [(data, {'name': 'test_1'}, 'points'),
                                 (data_2, {'name': 'test_2'}, 'points')])
