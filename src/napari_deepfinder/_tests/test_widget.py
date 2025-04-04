import numpy as np
import pytest
import collections
from scipy.ndimage import uniform_filter
from qtpy import QtCore

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
    # Check the viewfinder of the main viewer
    assert my_widget.main_view.layers[-1].name == "viewfinder_xy"
    # Check the viewfinder of the xz viewer
    assert my_widget.xz_view.layers[-1].name == "viewfinder_xz"
    # Check the viewfinder of the yz viewer
    assert my_widget.yz_view.layers[-1].name == "viewfinder_yz"
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
    qtbot.mouseClick(my_widget._add_point, QtCore.Qt.LeftButton)
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
    # check adding image
    checkerboard = np.indices((100, 100, 20)).sum(axis=0) % 2
    viewer.add_image(data=checkerboard, name="image_added")
    assert np.array_equal(my_widget.main_view.layers["image_added"].data, checkerboard)
    assert np.array_equal(my_widget.xz_view.layers["image_added"].data, checkerboard)
    assert np.array_equal(my_widget.yz_view.layers["image_added"].data, checkerboard)
    # check adding points
    viewer.add_points(data=None, ndim=3, name="points_added")
    assert np.array_equal(my_widget.main_view.layers["points_added"].data, np.empty([0, 3]))
    assert np.array_equal(my_widget.xz_view.layers["points_added"].data, np.empty([0, 3]))
    assert np.array_equal(my_widget.yz_view.layers["points_added"].data, np.empty([0, 3]))
    # check adding labels
    labels = np.zeros((100, 100, 20), dtype=int)
    viewer.add_labels(data=labels, name="labels_added")
    assert np.array_equal(my_widget.main_view.layers["labels_added"].data, labels)
    assert np.array_equal(my_widget.xz_view.layers["labels_added"].data, labels)
    assert np.array_equal(my_widget.yz_view.layers["labels_added"].data, labels)
    my_widget.checkbox.setChecked(False)
    my_widget._on_click_checkbox(False)
    my_widget.deleteLater()
    qtbot.wait(10)


@pytest.fixture
def Event():
    """Create a subclass for simulating vispy mouse events.
    Returns
    -------
    Event : Type
        A new tuple subclass named Event that can be used to create a
        NamedTuple object with fields "type", "is_dragging", and "modifiers".
    """
    return collections.namedtuple(
        'Event', field_names=['type', 'is_dragging', 'modifiers', 'position']
    )


# make_napari_viewer is a pytest fixture that returns a napari viewer object
def test_orthoslice_click(make_napari_viewer, qtbot, Event):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(data=np.random.random((100, 100, 20)), name='first')
    # create our widget, passing in the viewer
    my_widget = Orthoslice(viewer)
    # start the widget
    my_widget.checkbox.setChecked(True)
    my_widget._on_click_checkbox(True)
    # test start position
    assert my_widget.x == 50-1
    assert my_widget.y == 50-1
    assert my_widget.z == 10-1
    assert np.array_equal(viewer.layers[-1].data, np.array([[[50-1, 0, 10-1], [0, 100-2, 0]],
                                                            [[0, 50-1, 10-1], [100-2, 0, 0]]]))
    # click and test end position
    # Simulate click
    click_event = Event(
        type='mouse_press',
        is_dragging=False,
        modifiers=[],
        position=(75, 75),
    )
    my_widget.mouse_single_click(my_widget.main_view, click_event)
    assert my_widget.x == 75
    assert my_widget.y == 75
    assert my_widget.z == 10-1
    assert np.array_equal(viewer.layers[-1].data, np.array([[[75, 0, 10-1], [0, 100-2, 0]],
                                                            [[0, 75, 10-1], [100-2, 0, 0]]]))
    # Insert a layer while in orthoslice view
    viewer.add_image(data=np.random.random((100, 100, 20)), name='test')
    assert my_widget.yz_view.layers[-2].name == 'test'
    # Remove a layer while in orthoslice view
    viewer.layers.remove(viewer.layers['test'])
    assert my_widget.yz_view.layers[-2].name == 'first'
    my_widget.checkbox.setChecked(False)
    my_widget._on_click_checkbox(False)
    my_widget.deleteLater()
    qtbot.wait(10)
