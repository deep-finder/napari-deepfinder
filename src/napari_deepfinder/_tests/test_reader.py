from napari_deepfinder import napari_get_reader
import numpy as np
import mrcfile


# tmp_path is a pytest fixture
def test_reader(tmp_path):
    # write some fake data using your supported file format
    my_test_file = str(tmp_path / "file1.mrc")
    original_data = np.zeros((5, 5, 5), dtype=np.int8)
    original_data[1:4, 1:4, 1:4]
    with mrcfile.new(my_test_file) as mrc:
        mrc.set_data(original_data)

    # try to read it back in
    reader = napari_get_reader(my_test_file)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data_list = reader(my_test_file)
    assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
    layer_data_tuple = layer_data_list[0]
    assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0

    # make sure it's the same as it started
    np.testing.assert_allclose(original_data, layer_data_tuple[0])


def test_get_reader_pass():
    reader = napari_get_reader("fake.file")
    assert reader is None
