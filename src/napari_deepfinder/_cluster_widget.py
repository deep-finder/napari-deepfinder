from qtpy.QtWidgets import QWidget, QGridLayout, QComboBox, QPushButton, QLabel, QGroupBox, QVBoxLayout, QTextEdit, \
    QSpinBox, QFileDialog, QLineEdit
from qtpy import QtCore
import numpy as np
import napari
import napari.layers
from napari.qt.threading import create_worker
from deepfinder.inference import Cluster
from deepfinder.utils import core
from deepfinder.utils import objl as ol


class ClusterWidget(QWidget):
    print_signal = QtCore.Signal(str)  # signal for listening to prints of deepfinder

    def __init__(self, napari_viewer: napari.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.objlist = None

        self.print_signal.connect(self.on_print_signal)

        # Use this event because of bug in viewer.events.layers_change.connect() : it doesn't register name change
        napari_viewer.layers.events.connect(self._on_layer_change)

        self.setLayout(QVBoxLayout())
        # Input group
        self.group_input = QGroupBox('Input')
        self._input_layer_box = QComboBox()
        self.box_input = QGridLayout()
        # Label layer
        self.box_input.addWidget(QLabel('Labels layer:'), 0, 0, QtCore.Qt.AlignTop)
        self.box_input.addWidget(self._input_layer_box, 0, 1, 1, 2, QtCore.Qt.AlignTop)
        # Cluster radius
        self.cluster_radius = QSpinBox()
        self.cluster_radius.setValue(5)
        self.box_input.addWidget(QLabel('Cluster radius:'), 2, 0, QtCore.Qt.AlignTop)
        self.box_input.addWidget(self.cluster_radius, 2, 1, 1, 2, QtCore.Qt.AlignTop)
        # Size threshold
        self.size_threshold = QSpinBox()
        self.size_threshold.setValue(1)
        self.box_input.addWidget(QLabel('Size threshold:'), 3, 0, QtCore.Qt.AlignTop)
        self.box_input.addWidget(self.size_threshold, 3, 1, 1, 2, QtCore.Qt.AlignTop)
        # Set group
        self.group_input.setLayout(self.box_input)
        self.layout().addWidget(self.group_input)

        # Output group
        self.group_output = QGroupBox('Output')
        self.box_output = QGridLayout()
        self.box_output.addWidget(QLabel('Object list path:'), 0, 0, QtCore.Qt.AlignTop)
        self.output_path = QLineEdit()
        self.box_output.addWidget(self.output_path, 0, 1, 1, 2, QtCore.Qt.AlignTop)
        browse_btn_p = QPushButton('...')
        browse_btn_p.released.connect(self.browse_output)
        self.box_output.addWidget(browse_btn_p, 0, 3, 1, 1, QtCore.Qt.AlignTop)
        self.group_output.setLayout(self.box_output)
        self.layout().addWidget(self.group_output)
        # Launch
        self._launch_clustering = QPushButton("Launch")
        self._launch_clustering.clicked.connect(self._run)
        self.layout().addWidget(self._launch_clustering, QtCore.Qt.AlignTop)
        # Terminal output
        self.te_terminal_out = QTextEdit()
        self.te_terminal_out.setVisible(False)
        self.te_terminal_out.setReadOnly(True)
        self.layout().addWidget(self.te_terminal_out, QtCore.Qt.AlignTop)
        self._on_layer_change()

        self._on_layer_change()

    def browse_output(self):
        """Callback called when the browse output button is clicked"""
        file = QFileDialog.getSaveFileName(self, "Save file", "", "*.xml")
        if file[0] != "":
            if file[0][-4:] == '.xml':
                self.output_path.setText(file[0])
            else:
                self.output_path.setText(file[0]+'.xml')
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
            if isinstance(layer, napari.layers.labels.labels.Labels):
                if layer.name == current_text:
                    is_current_item_still_here = True
                self._input_layer_box.addItem(layer.name)
        if is_current_item_still_here:
            self._input_layer_box.setCurrentText(current_text)
        else:
            self._input_layer_box.setCurrentIndex(-1)

    def launch_process(self):
        # Get parameters from line edit widgets:
        cradius = int(self.cluster_radius.value())
        csize_thr = int(self.size_threshold.value())
        path_objl = self.output_path.text()

        # Initialize deepfinder:
        clust = Cluster(clustRadius=cradius)
        clust.sizeThr = csize_thr
        clust.set_observer(core.observer_gui(self.print_signal))

        # Load label map:
        clust.display('Loading label map ...')
        current_layer_text = self._input_layer_box.currentText()
        labelmap_not_converted = self.viewer.layers[current_layer_text].data
        # invert axes from z,y,x to x,y,z (weird convention)
        labelmap = np.transpose(labelmap_not_converted, (2, 1, 0))

        # Launch clustering (result stored in objlist)
        self.objlist = clust.launch(labelmap)

        # Save objlist:
        ol.write(self.objlist, path_objl)
        return path_objl

    def add_cluster(self, path):
        self.viewer.open(path, plugin='napari-deepfinder')
        self._launch_clustering.setEnabled(True)

    def _run(self):
        # save against edge cases where the name of the layer is modified and the add button is clicked just after
        old_text = self._input_layer_box.currentText()
        self._on_layer_change()
        current_layer_text = self._input_layer_box.currentText()
        if current_layer_text is not None and current_layer_text != "" and old_text == current_layer_text:
            self.te_terminal_out.setVisible(True)
            self._launch_clustering.setEnabled(False)
            worker = create_worker(self.launch_process)
            worker.returned.connect(self.add_cluster)
            worker.start()
