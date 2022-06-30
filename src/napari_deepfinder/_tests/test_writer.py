from napari_deepfinder import write_annotations_xml, write_labelmap, write_tomogram
import numpy as np
import os


def test_writing_one_layer(tmp_path):
    data = np.array([[0, 0, 0]])
    path = os.path.join(str(tmp_path), "test_labels")
    path_with_extension = os.path.join(str(tmp_path), "test_labels2.xml")
    write_annotations_xml(path, [(data, {'name': 'test_1'}, 'points')])
    write_annotations_xml(path_with_extension, [(data, {'name': 'test_1'}, 'points')])


def test_writing_multiple_layers(tmp_path):
    data = np.array([[0, 0, 0]])
    data_2 = np.array([[1, 1, 1], [0, 0, 0]])
    path = os.path.join(str(tmp_path), "test_labels")
    write_annotations_xml(path, [(data, {'name': 'test_1'}, 'points'),
                                 (data_2, {'name': 'test_2'}, 'points')])


def test_writing_labelmap(tmp_path):
    data = np.zeros((10, 10, 2), dtype=np.uint8)
    path = os.path.join(str(tmp_path), "test_labelmap")
    path_with_extension = os.path.join(str(tmp_path), "test_labelmap2.mrc")
    write_labelmap(path, data, {'name': 'test'})
    write_labelmap(path_with_extension, data, {'name': 'test'})


def test_writing_tomogram(tmp_path):
    data = np.zeros((10, 10, 2), dtype=np.float32)
    path = os.path.join(str(tmp_path), "test_tomo")
    path_with_extension = os.path.join(str(tmp_path), "test_tomo2.mrc")
    write_tomogram(path, data, {'name': 'test'})
    write_tomogram(path_with_extension, data, {'name': 'test'})

