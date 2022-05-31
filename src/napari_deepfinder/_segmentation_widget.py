from qtpy.QtWidgets import QWidget, QGridLayout, QComboBox, QPushButton, QLabel, QGroupBox, QVBoxLayout, QTextEdit, \
    QSpinBox, QCheckBox, QLineEdit, QFileDialog
from qtpy import QtCore
import napari
import napari.layers
from napari.qt.threading import create_worker
import numpy as np
import os
from deepfinder.inference import Segment
from deepfinder.utils import core
from deepfinder.utils import common as cm
from deepfinder.utils import smap as sm


class SegmentationWidget(QWidget):
    print_signal = QtCore.Signal(str)  # signal for listening to prints of deepfinder

    def __init__(self, napari_viewer: napari.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.labelmap = None

        self.print_signal.connect(self.on_print_signal)

        # Use this event because of bug in viewer.events.layers_change.connect() : it doesn't register name change
        napari_viewer.layers.events.connect(self._on_layer_change)

        self.setLayout(QVBoxLayout())
        # Input group
        self.group_input = QGroupBox('Input')
        self._input_layer_box = QComboBox()
        self.box_input = QGridLayout()
        # Image layer
        self.box_input.addWidget(QLabel('Image layer:'), 0, 0, QtCore.Qt.AlignTop)
        self.box_input.addWidget(self._input_layer_box, 0, 1, 1, 2, QtCore.Qt.AlignTop)
        # Weights
        self.box_input.addWidget(QLabel('Net weights path:'), 1, 0, QtCore.Qt.AlignTop)
        self.weights_path = QLineEdit()
        self.box_input.addWidget(self.weights_path, 1, 1, 1, 2, QtCore.Qt.AlignTop)
        browse_btn_weights = QPushButton('...')
        browse_btn_weights.released.connect(self.browse_weights)
        self.box_input.addWidget(browse_btn_weights, 1, 3, 1, 1, QtCore.Qt.AlignTop)
        # Number of classes
        self.nb_classes = QSpinBox()
        self.nb_classes.setValue(13)
        self.box_input.addWidget(QLabel('Number of classes:'), 2, 0, QtCore.Qt.AlignTop)
        self.box_input.addWidget(self.nb_classes, 2, 1, 1, 2, QtCore.Qt.AlignTop)
        # Patch size
        self.patch_size = QSpinBox()
        self.patch_size.setValue(80)
        self.patch_size.setMinimum(80)
        self.patch_size.setMaximum(200)
        self.patch_size.setSingleStep(4)
        self.box_input.addWidget(QLabel('Patch size:'), 3, 0, QtCore.Qt.AlignTop)
        self.box_input.addWidget(self.patch_size, 3, 1, 1, 2, QtCore.Qt.AlignTop)
        # Set group
        self.group_input.setLayout(self.box_input)
        self.layout().addWidget(self.group_input)

        # Output group
        self.group_output = QGroupBox('Output')
        self.box_output = QGridLayout()
        self.box_output.addWidget(QLabel('Label map path:'), 0, 0, QtCore.Qt.AlignTop)
        self.output_path = QLineEdit()
        self.box_output.addWidget(self.output_path, 0, 1, 1, 2, QtCore.Qt.AlignTop)
        browse_btn_output = QPushButton('...')
        browse_btn_output.released.connect(self.browse_output)
        self.box_output.addWidget(browse_btn_output, 0, 3, 1, 1, QtCore.Qt.AlignTop)
        self.bin_label_map = QCheckBox("Bin label map")
        self.box_output.addWidget(self.bin_label_map, 1, 0, QtCore.Qt.AlignTop)
        self.group_output.setLayout(self.box_output)
        self.layout().addWidget(self.group_output)
        # Launch
        self._launch_segmentation = QPushButton("Launch")
        self._launch_segmentation.clicked.connect(self._run)
        self.layout().addWidget(self._launch_segmentation, QtCore.Qt.AlignTop)
        # Terminal output
        self.te_terminal_out = QTextEdit()
        self.te_terminal_out.setVisible(False)
        self.te_terminal_out.setReadOnly(True)
        self.layout().addWidget(self.te_terminal_out, QtCore.Qt.AlignTop)
        self._on_layer_change()

    def browse_weights(self):
        """Callback called when the browse weights button is clicked"""
        file = QFileDialog.getOpenFileName(self, "Open file", "", "*.h5")
        if file[0] != "":
            self.weights_path.setText(file[0])
        else:
            print("No file selected")

    def browse_output(self):
        """Callback called when the browse output button is clicked"""
        file = QFileDialog.getSaveFileName(self, "Save file", "", "*.mrc")
        if file[0] != "":
            if file[0][-4:] == '.mrc':
                self.output_path.setText(file[0])
            else:
                self.output_path.setText(file[0]+'.mrc')
        else:
            print("No file selected")


    @QtCore.Slot(str)
    def on_print_signal(self, message):  # is called when signal is emmited. Signal passes str 'message' to slot
        self.te_terminal_out.append(message)

    def _on_layer_change(self, event=None):
        current_text = self._input_layer_box.currentText()
        self._input_layer_box.clear()
        is_current_item_still_here = False
        for layer in self.viewer.layers:
            if isinstance(layer, napari.layers.image.image.Image):
                if layer.name == current_text:
                    is_current_item_still_here = True
                self._input_layer_box.addItem(layer.name)
        if is_current_item_still_here:
            self._input_layer_box.setCurrentText(current_text)
        else:
            self._input_layer_box.setCurrentIndex(-1)

    def launch_process(self):
        # Get parameters from line edit widgets:
        Ncl = int(self.nb_classes.text())
        psize = int(self.patch_size.value())
        path_weights = self.weights_path.text()
        path_lmap = self.output_path.text()

        # Load data:
        current_layer_text = self._input_layer_box.currentText()
        self.data = self.viewer.layers[current_layer_text].data

        # Initialize segmentation:
        seg = Segment(Ncl=Ncl, path_weights=path_weights, patch_size=psize)
        seg.set_observer(core.observer_gui(self.print_signal))

        # Segment data:
        scoremaps = seg.launch(self.data)

        seg.display('Saving labelmap ...')
        # Get labelmap from scoremaps and save:
        labelmap_not_converted = sm.to_labelmap(scoremaps)
        # invert axes from z,y,x to x,y,z (weird convention)
        self.labelmap = np.transpose(labelmap_not_converted, (2, 1, 0))
        cm.write_array(self.labelmap, path_lmap)

        # Get binned labelmap and save:
        if self.bin_label_map.isChecked():
            s = os.path.splitext(path_lmap)
            scoremapsB = sm.bin(scoremaps)
            labelmapB_not_converted = sm.to_labelmap(scoremapsB)
            # invert axes from z,y,x to x,y,z (weird convention)
            labelmapB = np.transpose(labelmapB_not_converted, (2, 1, 0))
            cm.write_array(labelmapB, s[0] + '_binned' + s[1])

        seg.display('Finished !')
        return labelmap_not_converted

    def add_labels(self, labelmap):
        self.viewer.add_labels(labelmap)
        self._launch_segmentation.setEnabled(True)

    def _run(self):
        # save against edge cases where the name of the layer is modified and the add button is clicked just after
        old_text = self._input_layer_box.currentText()
        self._on_layer_change()
        current_layer_text = self._input_layer_box.currentText()
        if current_layer_text is not None and current_layer_text != "" and old_text == current_layer_text:
            self.te_terminal_out.setVisible(True)
            self._launch_segmentation.setEnabled(False)
            worker = create_worker(self.launch_process)
            worker.returned.connect(self.add_labels)
            worker.start()
