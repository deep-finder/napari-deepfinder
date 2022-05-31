from napari_deepfinder import Orthoslice
import numpy as np


# make_napari_viewer is a pytest fixture that returns a napari viewer object
def test_orthoslice(make_napari_viewer, qtbot):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 20)))
    # create our widget, passing in the viewer
    my_widget = Orthoslice(viewer)
    # start the widget
    my_widget.checkbox.setChecked(True)
    my_widget._on_click_checkbox(True)
    # Check the viewfinders of the main viewer
    assert my_widget.main_view.layers[-1].name == 'viewfinder_xy_y'
    assert my_widget.main_view.layers[-2].name == 'viewfinder_xy_x'
    # Check the viewfinders of the xz viewer
    assert my_widget.xz_view.layers[-1].name == 'viewfinder_xz_z'
    assert my_widget.xz_view.layers[-2].name == 'viewfinder_xz_x'
    # Check the viewfinders of the yz viewer
    assert my_widget.yz_view.layers[-1].name == 'viewfinder_yz_z'
    assert my_widget.yz_view.layers[-2].name == 'viewfinder_yz_y'
    my_widget.checkbox.setChecked(False)
    my_widget._on_click_checkbox(False)
    my_widget.deleteLater()
    # qtbot.wait(50)
    pass
