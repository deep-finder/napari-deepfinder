import numpy as np
from magicgui import magic_factory
from qtpy.QtWidgets import QWidget, QGridLayout, QComboBox, QPushButton, QLabel, QPlainTextEdit, QGroupBox
from qtpy import QtCore
import napari
import napari.layers
from scipy.ndimage import uniform_filter
import warnings


@magic_factory(auto_call=True)
def denoise_widget(
        viewer: 'napari.viewer.Viewer',
        image_layer: 'napari.layers.Image',
        filter_size: int = 3,
        activate_denoise=False,
):
    """
    Widget to denoise an image layer.
    When activated adds the denoised image layer on top of the old one and hides the old layer.

    Parameters
    ----------
    viewer : napari.viewer.Viewer
    image_layer: napari.layers.Image
    filter_size: int
    activate_denoise: bool
    """
    # Initialisation
    if not hasattr(denoise_widget, 'denoised_layer'):
        # persistant values initialisation
        denoise_widget.denoised_layer = None
        denoise_widget.original_layer = None
        denoise_widget.old_filter_size = filter_size
    if image_layer is None:
        denoise_widget.activate_denoise.value = False
        denoise_widget.activate_denoise.enabled = False
    else:
        if not denoise_widget.activate_denoise.get_value():
            denoise_widget.activate_denoise.enabled = True
        denoised_name = image_layer.name + '_denoised'
        if denoise_widget.denoised_layer is None:
            denoised_im = False
        else:
            denoised_im = True
        if activate_denoise and denoised_im is False:
            denoised_data = uniform_filter(image_layer.data, size=filter_size)
            denoise_widget.old_filter_size = filter_size
            # correctly insert layer
            denoised_im = napari.layers.Layer.create(denoised_data, {'name': denoised_name}, layer_type='image')
            insert_index = index_of_layer(viewer, image_layer) + 1
            viewer.layers.insert(insert_index, denoised_im)
            # store denoised and original layers persistently
            denoise_widget.denoised_layer = viewer.layers[insert_index]
            denoise_widget.original_layer = viewer.layers[image_layer.name]
            # raise warning to the user, that this name has already been taken
            real_name = denoise_widget.denoised_layer.name
            if denoised_name != real_name:
                for layer in viewer.layers:
                    if layer.name == denoised_name:
                        warnings.warn('Name %s already taken, so %s chosen' % (denoised_name, real_name))
            # dummy is a workaround, because of a bug in layers
            dummy = napari.layers.Layer.create(np.zeros((1, 1, 1)), {'name': 'dummy'}, layer_type='image')
            viewer.layers.insert(0, dummy)
            viewer.layers.remove(viewer.layers['dummy'])
            # correctly hide original image
            viewer.layers[image_layer.name].visible = False
            # correctly lock the image layer selector when denoising applied
            denoise_widget.image_layer.enabled = False
        elif activate_denoise and denoise_widget.old_filter_size != filter_size and denoised_im is True:
            denoise_widget.denoised_layer.data = uniform_filter(image_layer.data, size=filter_size)
            denoise_widget.denoised_layer.reset_contrast_limits()
            denoise_widget.old_filter_size = filter_size
        elif denoised_im and not activate_denoise:
            if index_of_layer(viewer, denoise_widget.denoised_layer) is False:
                if index_of_layer(viewer, denoise_widget.original_layer) is not False:
                    viewer.layers[denoise_widget.original_layer.name].visible = True
            else:
                if index_of_layer(viewer, denoise_widget.original_layer) is not False:
                    viewer.layers[denoise_widget.original_layer.name].visible = True
                    viewer.layers.remove(viewer.layers[denoise_widget.denoised_layer.name])
            # return to init state
            denoise_widget.image_layer.enabled = True
            denoise_widget.denoised_layer = None
            denoise_widget.original_layer = None


@magic_factory(auto_call=True, call_button="Reorder layers")
def reorder_widget(viewer: 'napari.viewer.Viewer'):
    """
    Widget to reorder the layers respecting the following order from bottom to top:
        - Image
        - Labels
        - Points
        - All other layer types

    Parameters
    ----------
    viewer : napari.viewer.Viewer
    """
    reorder(viewer)


class AddPointsWidget(QWidget):
    """
    Widget to add points to layer.
    This is especially designed for tomogram annotation in Orthoslice view.
    """
    def __init__(self, napari_viewer: napari.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        # Use this event because of bug in viewer.events.layers_change.connect() : it doesn't register name change
        napari_viewer.layers.events.connect(self._on_layer_change)

        self.setLayout(QGridLayout())
        # Info box for annotation
        self.group_info = QGroupBox('Information')
        self.box_info = QGridLayout()
        self.text_info = QPlainTextEdit(
            """For annotation please respect the following convention for the export to work well:
        - each points layer needs to end with "_classNumber" (e.g.: ribosome_1)
        - the class numbers need to range from 1 to number of classes"""
        )
        self.text_info.setReadOnly(True)
        self.box_info.addWidget(self.text_info, 0, 0, QtCore.Qt.AlignTop)
        self.group_info.setLayout(self.box_info)
        self.layout().addWidget(self.group_info, 0, 0, 1, 3)
        # Add points
        self._input_layer_box = QComboBox()
        self._add_point = QPushButton("Add point")
        self._add_point.clicked.connect(self._run)
        self.layout().addWidget(QLabel('Points layer:'), 1, 0, 1, 1)
        self.layout().addWidget(self._input_layer_box, 1, 1, 1, 2)
        self.layout().addWidget(self._add_point, 2, 0, 1, 3)
        self.layout().addWidget(QWidget(), 1, QtCore.Qt.AlignTop)
        self._on_layer_change()

    def _on_layer_change(self, event=None):
        current_text = self._input_layer_box.currentText()
        self._input_layer_box.clear()
        is_current_item_still_here = False
        for layer in self.viewer.layers:
            if isinstance(layer, napari.layers.points.points.Points):
                if layer.name == current_text:
                    is_current_item_still_here = True
                self._input_layer_box.addItem(layer.name)
        if is_current_item_still_here:
            self._input_layer_box.setCurrentText(current_text)
        else:
            self._input_layer_box.setCurrentIndex(-1)

    def _run(self):
        # save against edge cases where the name of the layer is modified and the add button is clicked just after
        old_text = self._input_layer_box.currentText()
        self._on_layer_change()
        current_layer_text = self._input_layer_box.currentText()
        if current_layer_text is not None and current_layer_text != "" and old_text == current_layer_text:
            layer = self.viewer.layers[current_layer_text]
            layer.add(self.viewer.dims.current_step)


def reorder(viewer):
    new_list = viewer.layers
    old_list = new_list.copy()
    old_order = [check_instance(i) for i in old_list]
    while sorted(old_order) != old_order:
        new_list = viewer.layers
        old_list = new_list.copy()
        old_order = [check_instance(i) for i in old_list]
        old_index = [i for i in range(len(old_order))]
        zipped_old = zip(old_order, old_index)
        zipped_new = sorted(zipped_old)
        for i, (order, index) in enumerate(zipped_new):
            if index != i:
                new_list.move(index, i)
                break


def check_instance(layer_object):
    # order: first images, then points, then labels
    image = napari.layers.image.image.Image
    points = napari.layers.points.points.Points
    labels = napari.layers.labels.labels.Labels
    type_order = np.array([image, points, labels])
    for i, classobj in enumerate(type_order):
        if isinstance(layer_object, classobj):
            return i
    # Else, place on top for layers that are not in the type_order list
    return len(type_order)


def index_of_layer(viewer, layer):
    for i in range(len(viewer.layers)):
        if viewer.layers[i] == layer:
            return i
    # if not in list return false, useful for the widget
    return False
    # raise ValueError('could not find layer in viewer.layers list')
