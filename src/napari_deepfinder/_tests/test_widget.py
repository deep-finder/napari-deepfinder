import numpy as np
from scipy.ndimage import uniform_filter
from qtpy.QtCore import Qt

from napari_deepfinder import (
    AddPointsWidget,
    ClusterWidget,
    Orthoslice,
    SegmentationWidget,
    reorder_widget,
    denoise_widget
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
    assert np.array_equal(viewer.layers["test_layer"].data, np.empty([0, 3]))
    qtbot.mouseClick(my_widget._add_point, Qt.LeftButton)
    assert np.array_equal(viewer.layers["test_layer"].data, np.array([[256., 256., 256.]]))
    my_widget.deleteLater()
    qtbot.wait(10)


def test_reorder_layers(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    my_widget = reorder_widget()
    viewer.add_points(data=None, ndim=3, name="points")
    viewer.add_labels(data=np.zeros((512, 512), dtype=int), name="labels")
    viewer.add_points(data=None, ndim=3, name="points2")
    viewer.add_image(data=np.zeros((512, 512, 200)), name="image")
    assert [layer.name for layer in viewer.layers] == ["points", "labels", "points2", "image"]
    my_widget(viewer)
    assert [layer.name for layer in viewer.layers] == ["image", "points", "points2", "labels"]
    qtbot.wait(10)


def test_denoise_widget(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    my_widget = denoise_widget()
    # Add image
    checkerboard = np.indices((10, 10)).sum(axis=0) % 2
    viewer.add_image(data=checkerboard, name="image")
    filter_size = 2
    filtered_image = uniform_filter(checkerboard, size=filter_size)
    my_widget(viewer, viewer.layers['image'], 2, True)
    assert np.array_equal(viewer.layers["image_denoised"].data, filtered_image)


def test_orthoslice_add_layer(make_napari_viewer, qtbot):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 20)))
    # create our widget, passing in the viewer
    my_widget = Orthoslice(viewer)
    # start the widget
    my_widget.checkbox.setChecked(True)
    my_widget._on_click_checkbox(True)
    checkerboard = np.indices((10, 10)).sum(axis=0) % 2
    viewer.add_image(data=checkerboard, name="image_added")
    assert np.array_equal(my_widget.main_view.layers["image_added"].data, checkerboard)
    assert np.array_equal(my_widget.xz_view.layers["image_added"].data, checkerboard)
    assert np.array_equal(my_widget.yz_view.layers["image_added"].data, checkerboard)
    my_widget.checkbox.setChecked(False)
    my_widget._on_click_checkbox(False)
    my_widget.deleteLater()
    qtbot.wait(10)
