import numpy as np

from napari_deepfinder import (
    AddPointsWidget,
    ClusterWidget,
    Orthoslice,
    SegmentationWidget,
)


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
    assert my_widget.main_view.layers[-1].name == "viewfinder_xy_y"
    assert my_widget.main_view.layers[-2].name == "viewfinder_xy_x"
    # Check the viewfinders of the xz viewer
    assert my_widget.xz_view.layers[-1].name == "viewfinder_xz_z"
    assert my_widget.xz_view.layers[-2].name == "viewfinder_xz_x"
    # Check the viewfinders of the yz viewer
    assert my_widget.yz_view.layers[-1].name == "viewfinder_yz_z"
    assert my_widget.yz_view.layers[-2].name == "viewfinder_yz_y"
    my_widget.checkbox.setChecked(False)
    my_widget._on_click_checkbox(False)
    my_widget.deleteLater()
    qtbot.wait(10)


def test_segmentation(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    my_widget = SegmentationWidget(viewer)
    assert int(my_widget.nb_classes.text()) == 13
    my_widget.nb_classes.setValue(15)
    assert int(my_widget.nb_classes.text()) == 15
    my_widget.deleteLater()
    qtbot.wait(10)


def test_clustering(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    my_widget = ClusterWidget(viewer)
    assert int(my_widget.cluster_radius.text()) == 5
    my_widget.cluster_radius.setValue(10)
    assert int(my_widget.cluster_radius.text()) == 10
    my_widget.deleteLater()
    qtbot.wait(10)


def test_add_points(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    my_widget = AddPointsWidget(viewer)
    viewer.add_points(data=None, ndim=3, name="test_layer")
    my_widget._input_layer_box.setCurrentText("test_layer")
    my_widget._add_point.toggle()
    assert viewer.layers["test_layer"].data != np.array([])
    my_widget.deleteLater()
    qtbot.wait(10)
