from napari import Viewer, layers
from napari.settings import SETTINGS
import numpy as np
from typing import Optional
from qtpy.QtWidgets import QWidget, QHBoxLayout, QDesktopWidget, QCheckBox
from qtpy import QtCore


# TODO: add "scroll bar" sync
# TODO: clean up of the code, and basic documentation
class Orthoslice(QWidget):
    """Orthoslice widget"""

    def __init__(self, viewer: Viewer):
        super().__init__()
        self.main_view = viewer
        self.x_max: Optional[int] = None
        self.y_max: Optional[int] = None
        self.z_max: Optional[int] = None
        self.old_layer_names: Optional[list[str]] = []
        self.xz_view: Optional[Viewer] = None
        self.yz_view: Optional[Viewer] = None
        self.viewfinder_xz: Optional[layers.Layer] = None
        self.viewfinder_xy: Optional[layers.Layer] = None
        self.viewfinder_yz: Optional[layers.Layer] = None
        self.x: Optional[float] = None
        self.y: Optional[float] = None
        self.z: Optional[float] = None
        self.viewer_list = [self.main_view, self.xz_view, self.yz_view]
        self.gen_zoom_factor: Optional[float] = None
        # Attributes for the center (viewer and old position) when zoom triggered
        self.old_cameras = None
        self.viewer_center_moved = None
        # Don't set init width too low, otherwise the lines might "disappear" sometimes
        self.init_width = 2.3
        # Graphical part
        self.checkbox = QCheckBox('Orthoslice')
        self.checkbox.setChecked(False)
        self.checkbox.clicked.connect(self._on_click_checkbox)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.checkbox, 1, QtCore.Qt.AlignTop)
        self.running = False

    def _on_click_checkbox(self, value):
        if value:
            layer_not_compatible = False
            for layer in self.main_view.layers:
                if layer.ndim != 3:
                    layer_not_compatible = True
            if not self.main_view.layers:
                self.checkbox.setChecked(False)
                raise UserWarning('No layers, impossible to activate orthoslice view')
            elif layer_not_compatible:
                self.checkbox.setChecked(False)
                raise UserWarning('A layer is not compatible with 3D view (wrong dimension)')
            else:
                self.start_ortho()
                self.running = True
        else:
            if self.running:
                self.end_ortho()
                self.running = False

    def mouse_click_drag(self, viewer: Viewer, event):
        old_camera = viewer.camera.copy()
        dragged = False
        yield
        # on move
        while event.type == 'mouse_move':
            dragged = True
            # already trigger drag while moving
            if dragged and event.button == 2:
                # zoom is now handled by zoom event!
                # self.zoom(viewer, event)
                pass
            if dragged and event.button == 1:
                self.mouse_drag(viewer, event, old_camera)
                old_camera = viewer.camera.copy()
            yield
        # on release
        if dragged:
            # Dragged left click
            if event.button == 1:
                self.mouse_drag(viewer, event, old_camera)
                old_camera = viewer.camera.copy()
            # Dragged right click
            if event.button == 2:
                # zoom is now handled by zoom event!
                # self.zoom(viewer, event)
                pass
        else:
            # Simple left click
            if event.button == 1:
                self.mouse_single_click(viewer, event)
            # Simple right click
            if event.button == 2:
                pass

    def mouse_single_click(self, viewer, event):
        # TODO: what to do with the sliders?? (they can also change the positions)
        for i, pos in enumerate(event.position):
            if i == 0:
                if pos > self.x_max:
                    self.x = self.x_max
                elif pos < 0:
                    self.x = 0
                else:
                    self.x = pos
            if i == 1:
                if pos > self.y_max:
                    self.y = self.y_max
                elif pos < 0:
                    self.y = 0
                else:
                    self.y = pos
            if i == 2:
                if pos > self.z_max:
                    self.z = self.z_max
                elif pos < 0:
                    self.z = 0
                else:
                    self.z = pos
        self.x = np.round(self.x)
        self.y = np.round(self.y)
        self.z = np.round(self.z)
        for view in self.viewer_list:
            view.dims.current_step = [self.x, self.y, self.z]
        self.update_viewfinders()

    def update_viewfinders(self):
        # viewfinder for xz
        self.viewfinder_xz.data[0] = [[self.x, self.y, 0], [0, 0, self.z_max]]
        self.viewfinder_xz.data[1] = [[0, self.y, self.z], [self.x_max, 0, 0]]
        # Viewfinder for xy
        self.viewfinder_xy.data[0] = [[self.x, 0, self.z], [0, self.y_max, 0]]
        self.viewfinder_xy.data[1] = [[0, self.y, self.z], [self.x_max, 0, 0]]
        # Viewfinder for yz
        self.viewfinder_yz.data[0] = [[self.x, self.y, 0], [0, 0, self.z_max]]
        self.viewfinder_yz.data[1] = [[self.x, 0, self.z], [0, self.y_max, 0]]
        # TODO: replace the dirty fix to update viewfinders
        # dirty fix
        width = self.init_width / self.gen_zoom_factor
        self.viewfinder_xz.edge_width = width
        self.viewfinder_xy.edge_width = width
        self.viewfinder_yz.edge_width = width
        # refresh not working
        # self.refresh_viewfinders()

    def refresh_viewfinders(self):
        self.viewfinder_xz.refresh()
        self.viewfinder_xy.refresh()
        self.viewfinder_yz.refresh()

    def mouse_drag(self, viewer: Viewer, event, old_camera):
        xyz_l = viewer.camera.center
        diff = np.array(xyz_l) - np.array(old_camera.center)
        dragged_viewer_order = viewer.dims.order
        if dragged_viewer_order == (2, 1, 0):
            view1 = self.viewer_list[1]
            new_tuple = (view1.camera.center[0],
                         view1.camera.center[1],
                         view1.camera.center[2] + diff[2])
            view1.camera.center = new_tuple
            view2 = self.viewer_list[2]
            new_tuple = (view2.camera.center[0],
                         view2.camera.center[1] + diff[1],
                         view2.camera.center[2])
            view2.camera.center = new_tuple
        elif dragged_viewer_order == (1, 2, 0):
            view1 = self.viewer_list[0]
            new_tuple = (view1.camera.center[0],
                         view1.camera.center[1],
                         view1.camera.center[2] + diff[2])
            view1.camera.center = new_tuple
            view2 = self.viewer_list[2]
            new_tuple = (view2.camera.center[0],
                         view2.camera.center[1],
                         view2.camera.center[2] + diff[1])
            view2.camera.center = new_tuple
        elif dragged_viewer_order == (0, 1, 2):
            view1 = self.viewer_list[0]
            new_tuple = (view1.camera.center[0],
                         view1.camera.center[1] + diff[1],
                         view1.camera.center[2])
            view1.camera.center = new_tuple
            view2 = self.viewer_list[1]
            new_tuple = (view2.camera.center[0],
                         view2.camera.center[1] + diff[2],
                         view2.camera.center[2])
            view2.camera.center = new_tuple

    def disconnect_zoom(self):
        self.main_view.camera.events.zoom.disconnect(self.zoom)
        self.xz_view.camera.events.zoom.disconnect(self.zoom)
        self.yz_view.camera.events.zoom.disconnect(self.zoom)
        self.disconnect_center()

    def connect_zoom(self):
        self.main_view.camera.events.zoom.connect(self.zoom, position='last')
        self.xz_view.camera.events.zoom.connect(self.zoom, position='last')
        self.yz_view.camera.events.zoom.connect(self.zoom, position='last')
        self.connect_center()

    def connect_center(self):
        # Init old cameras
        self.old_cameras = self.get_old_cameras()
        # connect center position callbacks
        self.main_view.camera.events.center.connect(self.old_center_main, position='last')
        self.xz_view.camera.events.center.connect(self.old_center_xz, position='last')
        self.yz_view.camera.events.center.connect(self.old_center_yz, position='last')

    def disconnect_center(self):
        self.main_view.camera.events.center.disconnect(self.old_center_main)
        self.xz_view.camera.events.center.disconnect(self.old_center_xz)
        self.yz_view.camera.events.center.disconnect(self.old_center_yz)

    def old_center_main(self, event):
        old_camera = self.old_cameras[0]
        self.viewer_center_moved = self.main_view
        self.disconnect_center()
        self.mouse_drag(self.viewer_center_moved, None, old_camera)
        self.connect_center()
        self.old_cameras = self.get_old_cameras()

    def old_center_xz(self, event):
        old_camera = self.old_cameras[1]
        self.viewer_center_moved = self.xz_view
        self.disconnect_center()
        self.mouse_drag(self.viewer_center_moved, None, old_camera)
        self.connect_center()
        self.old_cameras = self.get_old_cameras()

    def old_center_yz(self, event):
        old_camera = self.old_cameras[2]
        self.viewer_center_moved = self.yz_view
        self.disconnect_center()
        self.mouse_drag(self.viewer_center_moved, None, old_camera)
        self.connect_center()
        self.old_cameras = self.get_old_cameras()

    def get_old_cameras(self):
        return [self.main_view.camera.copy(), self.xz_view.camera.copy(), self.yz_view.camera.copy()]

    def zoom(self, event):
        self.disconnect_zoom()
        change = self.unify_camera_zoom()
        if change:
            width = self.init_width / self.gen_zoom_factor
            self.viewfinder_xz.edge_width = width
            self.viewfinder_xy.edge_width = width
            self.viewfinder_yz.edge_width = width
            self.refresh_viewfinders()
        self.connect_zoom()

    def unify_camera_zoom(self):
        zooms = [self.main_view.camera.zoom, self.xz_view.camera.zoom, self.yz_view.camera.zoom]
        for idx, i in enumerate(zooms):
            # dirty bugfix because dragging the layer around slightly modifies the zoom level
            if i > self.gen_zoom_factor + 0.0001 or i < self.gen_zoom_factor - 0.0001:
                self.gen_zoom_factor = i
                self.main_view.camera.zoom = self.gen_zoom_factor
                self.xz_view.camera.zoom = self.gen_zoom_factor
                self.yz_view.camera.zoom = self.gen_zoom_factor
                return True
        return False

    def place_windows(self):
        self.xz_view.dims.transpose()
        geom = QDesktopWidget().availableGeometry()
        height = geom.height() // 2
        width = geom.width() // 2
        SETTINGS.application.window_size = (width, height)
        xy_geom = (0, 0, width, height)
        yz_geom = (0 + width, 0, width, height)
        xz_geom = (0, height, width, height)
        zipped_list = zip(self.viewer_list, [xy_geom, xz_geom, yz_geom])
        for viewer, geo in zipped_list:
            w = viewer.window._qt_window
            w.setGeometry(*geo)

    def start_ortho(self):
        self.main_view.window.qt_viewer.set_welcome_visible(False)
        # force 2d display
        if self.main_view.dims.ndisplay != 2:
            self.main_view.dims.ndisplay = 2
        self.main_view.dims.order = [2, 0, 1]
        self.x_max = int(self.main_view.dims.range[0][1]) - 1
        self.y_max = int(self.main_view.dims.range[1][1]) - 1
        self.z_max = int(self.main_view.dims.range[2][1]) - 1
        selection = self.main_view.layers.selection.copy()
        self.gen_zoom_factor = self.main_view.camera.zoom
        self.x, self.y, self.z = self.main_view.dims.current_step

        viewfinder_data_xz = np.zeros(shape=(2, 2, 3), dtype=np.float32)
        viewfinder_data_xy = np.zeros(shape=(2, 2, 3), dtype=np.float32)
        viewfinder_data_yz = np.zeros(shape=(2, 2, 3), dtype=np.float32)
        # Viewfinder for xz
        viewfinder_data_xz[0] = [[self.x, self.y,  0], [0, 0, self.z_max]]
        viewfinder_data_xz[1] = [[0, self.y, self.z], [self.x_max, 0, 0]]
        # Viewfinder for xy
        viewfinder_data_xy[0] = [[self.x, 0, self.z], [0, self.y_max, 0]]
        viewfinder_data_xy[1] = [[0, self.y, self.z], [self.x_max, 0, 0]]
        # Viewfinder for yz
        viewfinder_data_yz[0] = [[self.x, self.y, 0], [0, 0, self.z_max]]
        viewfinder_data_yz[1] = [[self.x, 0, self.z], [0, self.y_max, 0]]

        self.main_view.add_vectors(viewfinder_data_xy,
                                   name='viewfinder_xy',
                                   vector_style='line',
                                   edge_width=self.init_width / self.gen_zoom_factor)
        self.viewfinder_xy = self.main_view.layers[-1]

        # set window size
        geom = QDesktopWidget().availableGeometry()
        height = geom.height() // 2
        width = geom.width() // 2
        SETTINGS.application.window_size = (width, height)
        self.xz_view = Viewer(title='xz', order=[1, 0, 2])
        self.xz_view.window.qt_viewer.set_welcome_visible(False)
        self.yz_view = Viewer(title='yz', order=[0, 1, 2])
        self.yz_view.window.qt_viewer.set_welcome_visible(False)

        # Hide layer list and controls in secondary viewers, Future warning!!
        self.xz_view.window.qt_viewer.dockLayerControls.setVisible(False)
        self.xz_view.window.qt_viewer.dockLayerList.setVisible(False)
        self.yz_view.window.qt_viewer.dockLayerControls.setVisible(False)
        self.yz_view.window.qt_viewer.dockLayerList.setVisible(False)
        # Remove menu bar in secondary viewers
        self.xz_view.window.main_menu.close()
        self.yz_view.window.main_menu.close()

        self.main_view.mouse_drag_callbacks.append(self.mouse_click_drag)
        # zoom is now handled by zoom event!
        # self.main_view.mouse_wheel_callbacks.append(self.zoom)

        self.xz_view.mouse_drag_callbacks.append(self.mouse_click_drag)
        # zoom is now handled by zoom event!
        # self.xz_view.mouse_wheel_callbacks.append(self.zoom)
        self.yz_view.mouse_drag_callbacks.append(self.mouse_click_drag)
        # zoom is now handled by zoom event!
        # self.yz_view.mouse_wheel_callbacks.append(self.zoom)
        self.init_layers()

        self.xz_view.add_vectors(viewfinder_data_xz,
                                 name='viewfinder_xz',
                                 vector_style='line',
                                 edge_width=self.init_width / self.gen_zoom_factor)
        self.viewfinder_xz = self.xz_view.layers[-1]

        self.yz_view.add_vectors(viewfinder_data_yz,
                                 name='viewfinder_yz',
                                 vector_style='line',
                                 edge_width=self.init_width / self.gen_zoom_factor)
        self.viewfinder_yz = self.yz_view.layers[-1]

        self.xz_view.dims.order = [1, 0, 2]
        self.yz_view.dims.order = [0, 1, 2]
        # fix weird bug in axis display order (y,x) instead of (x,y) of main viewer
        self.main_view.dims.transpose()

        self.xz_view.camera.zoom = self.gen_zoom_factor
        self.yz_view.camera.zoom = self.gen_zoom_factor
        self.viewer_list = [self.main_view, self.xz_view, self.yz_view]

        # Init the update of the layers of secondary viewers
        self.init_layer_connection()
        # Update the selected layers of secondary viewers
        self.main_view.layers.selection.events.changed.connect(self.layer_selection, position='last')
        self.main_view.layers.selection = selection
        # Update when added/removed layers
        self.main_view.layers.events.removed.connect(self.layer_removed)
        self.main_view.layers.events.inserted.connect(self.layer_inserted, position="last")
        self.main_view.layers.events.reordered.connect(self.layer_reordered)

        # force viewers cameras to be centered
        # disconnect zoom to be able to set centers, without the setting of the center interfering
        self.disconnect_zoom()
        self.main_view.camera.center = (self.z_max // 2, self.y_max // 2, self.x_max // 2)
        self.yz_view.camera.center = (self.z_max //2, self.y_max // 2, self.x_max // 2)
        self.xz_view.camera.center = (self.z_max //2, self.y_max // 2, self.x_max // 2)
        # Now synchronise zoom factors and update viewfinders!
        self.connect_zoom()
        self.update_viewfinders()

        # Place windows
        self.place_windows()

    def init_layers(self):
        for layer in self.main_view.layers:
            self.sync_layer(None, init=True, layer=layer)
            self.old_layer_names.append(layer.name)

    def layer_selection(self):
        self.main_view.layers.selection.events.changed.disconnect(self.layer_selection)
        selection = self.main_view.layers.selection
        # delete viewfinders from the selection if they are selected
        new_selection = set()
        for layer in selection:
            if layer != self.viewfinder_xy:
                new_selection.add(layer)
        self.main_view.layers.selection = new_selection
        self.main_view.layers.selection.events.changed.connect(self.layer_selection, position='last')
        xz_set = {self.xz_view.layers[layer.name] for layer in new_selection}
        yz_set = {self.yz_view.layers[layer.name] for layer in new_selection}
        self.xz_view.layers.selection = xz_set
        self.yz_view.layers.selection = yz_set

    def init_layer_connection(self):
        self.viewfinder_on_top()
        for i in range(len(self.main_view.layers[:-1])):
            layer = self.main_view.layers[i]
            layer.events.connect(self.sync_layer)
        # Lock name of viewfinders
        self.viewfinder_xy.events.name.connect(self.keep_viewfinder_xy)
        self.viewfinder_xz.events.name.connect(self.keep_viewfinder_xz)
        self.viewfinder_yz.events.name.connect(self.keep_viewfinder_yz)

    def layer_disconnect(self):
        self.viewfinder_on_top()
        for i in range(len(self.main_view.layers[:-1])):
            layer = self.main_view.layers[i]
            layer.events.disconnect(self.sync_layer)
        # Disconnect the name locking of viewfinders
        self.viewfinder_xy.events.name.disconnect(self.keep_viewfinder_xy)
        self.viewfinder_xz.events.name.disconnect(self.keep_viewfinder_xz)
        self.viewfinder_yz.events.name.disconnect(self.keep_viewfinder_yz)

    def keep_viewfinder_xy(self, event):
        event.source.name = "viewfinder_xy"
        
    def keep_viewfinder_xz(self, event):
        event.source.name = "viewfinder_xz"
        
    def keep_viewfinder_yz(self, event):
        event.source.name = "viewfinder_yz"
    
    def layer_removed(self, event):
        self.old_layer_names = [layer.name for layer in self.main_view.layers]
        layer_removed = event.value
        if layer_removed != self.viewfinder_xy:
            xz_layer = self.xz_view.layers[layer_removed.name]
            yz_layer = self.yz_view.layers[layer_removed.name]
            self.xz_view.layers.remove(xz_layer)
            self.yz_view.layers.remove(yz_layer)

    def layer_inserted(self, event):
        layer_inserted = event.value
        image = layers.image.image.Image
        points = layers.points.points.Points
        labels = layers.labels.labels.Labels
        if (
                isinstance(layer_inserted, image)
                or isinstance(layer_inserted, points)
                or isinstance(layer_inserted, labels)
        ):
            index = index_of_layer(self.main_view, self.main_view.layers[layer_inserted.name])
            # update old layer names
            self.old_layer_names = [layer.name for layer in self.main_view.layers]
            self.sync_layer(None, init=True, layer=self.main_view.layers[index], insert=True, index=index)
            # conclusion: until this function is not finished: layer not added!!
            # So the reordering needs to be triggered after... else there are bugs
            nb_layers = len(self.main_view.layers)
            if index in [nb_layers - 2, nb_layers - 1]:
                self.xz_view.layers.move(index, nb_layers - 2)
                self.yz_view.layers.move(index, nb_layers - 2)
                self.main_view.layers.move(index, nb_layers - 2)
                self.old_layer_names = [layer.name for layer in self.main_view.layers]
            else:
                # workaround bug insert layer
                self.main_view.layers.events.inserted.disconnect(self.layer_inserted)
                self.main_view.layers.events.removed.disconnect(self.layer_removed)
                self.main_view.layers.selection.events.changed.disconnect(self.layer_selection)
                for viewer in self.viewer_list:
                    dummy = layers.Layer.create(np.zeros((1, 1, 1)), {'name': 'dummy'}, layer_type='image')
                    viewer.layers.insert(nb_layers - 2, dummy)
                    viewer.layers.remove(viewer.layers[nb_layers - 2])
                self.main_view.layers.selection.events.changed.connect(self.layer_selection, position='last')
                self.main_view.layers.events.inserted.connect(self.layer_inserted, position='last')
                self.main_view.layers.events.removed.connect(self.layer_removed)
            # synchronise this new layer (connect it)
            self.main_view.layers[layer_inserted.name].events.connect(self.sync_layer)
        else:
            self.main_view.layers.events.removed.disconnect(self.layer_removed)
            self.main_view.layers.remove(layer_inserted)
            self.main_view.layers.events.removed.connect(self.layer_removed)
            raise UserWarning("Only image, points or labels supported when adding layer in plugin")

    def layer_reordered(self, event):
        # check if viewfinders are on top
        self.main_view.layers.events.reordered.disconnect(self.layer_reordered)
        self.viewfinder_on_top()
        self.main_view.layers.events.reordered.connect(self.layer_reordered)
        main_layer_list = [layer.name for layer in self.main_view.layers]
        for index, name in enumerate(main_layer_list):
            if name == 'viewfinder_xy':
                xz_index = index_of_layer(self.xz_view, self.xz_view.layers['viewfinder_xz'])
                yz_index = index_of_layer(self.yz_view, self.yz_view.layers['viewfinder_yz'])
            elif name == 'viewfinder_xy':
                xz_index = index_of_layer(self.xz_view, self.xz_view.layers['viewfinder_xz'])
                yz_index = index_of_layer(self.yz_view, self.yz_view.layers['viewfinder_yz'])
            else:
                xz_index = index_of_layer(self.xz_view, self.xz_view.layers[name])
                yz_index = index_of_layer(self.yz_view, self.yz_view.layers[name])
            if index != xz_index:
                self.xz_view.layers.move(xz_index, index)
                self.yz_view.layers.move(yz_index, index)

    def viewfinder_on_top(self):
        index_0 = index_of_layer(self.main_view, self.viewfinder_xy)
        nb_layers = len(self.main_view.layers)
        if index_0 != nb_layers - 1:
            self.main_view.layers.move(index_0, nb_layers)
            self.old_layer_names = [layer.name for layer in self.main_view.layers]

    def sync_layer(self, event, init=False, layer: Optional[layers.Layer] = None, insert=False,
                   index: Optional[int] = None):
        image = layers.image.image.Image
        points = layers.points.points.Points
        labels = layers.labels.labels.Labels
        secondary_viewers = [self.xz_view, self.yz_view]
        if not init:
            layer = event.source
            # handle name change in a "dirty" way
            index = index_of_layer(self.main_view, layer)
            if (
                index is not False  # The layer must be found in layers list!
                and layer.name != self.old_layer_names[index]
                and index != len(self.main_view.layers) - 1  # Do not change the name of the viewfinders!
            ):
                for view in secondary_viewers:
                    view.layers[index].name = layer.name
                self.old_layer_names[index] = layer.name
        # TODO: could this be done with copy?
        if isinstance(layer, image):
            for view in secondary_viewers:
                if init:
                    name = layer.name
                    data = layer.data
                    if insert:
                        layer_tmp = layers.Layer.create(data, {'name': name}, layer_type='image')
                        view.layers.insert(index, layer_tmp)
                    else:
                        view.add_image(data, name=name)
                view.layers[layer.name].data = layer.data
                view.layers[layer.name].opacity = layer.opacity
                view.layers[layer.name].contrast_limits = layer.contrast_limits
                view.layers[layer.name].gamma = layer.gamma
                view.layers[layer.name].colormap = layer.colormap
                view.layers[layer.name].blending = layer.blending
                view.layers[layer.name].interpolation = layer.interpolation
                view.layers[layer.name].visible = layer.visible
        elif isinstance(layer, points):
            # force out of slice display
            layer.events.disconnect(self.sync_layer)
            layer.out_of_slice_display = True
            layer.events.connect(self.sync_layer)
            for view in secondary_viewers:
                if init:
                    # FORCE ndim = 3 (annotations in 3D)
                    name = layer.name
                    data = layer.data
                    size = layer.size
                    face_color = layer.face_color
                    out_of_slice_display = layer.out_of_slice_display
                    if insert:
                        layer_tmp = layers.Layer.create(data, {'name': name, 'ndim': 3}, layer_type='points')
                        view.layers.insert(index, layer_tmp)
                    else:
                        view.add_points(data,
                                        ndim=3,
                                        name=name,
                                        out_of_slice_display=out_of_slice_display)
                view.layers[layer.name].data = layer.data
                view.layers[layer.name].opacity = layer.opacity
                view.layers[layer.name].size = layer.size
                view.layers[layer.name].blending = layer.blending
                view.layers[layer.name].symbol = layer.symbol
                if layer.face_color.size != 0:
                    view.layers[layer.name].face_color = layer.face_color
                if layer.edge_color.size != 0:
                    view.layers[layer.name].edge_color = layer.edge_color
                view.layers[layer.name].text = layer.text
                view.layers[layer.name].out_of_slice_display = layer.out_of_slice_display
                # Selected data is buggy
                # view.layers[layer.name].selected_data = layer.selected_data
                view.layers[layer.name].visible = layer.visible
        elif isinstance(layer, labels):
            for view in secondary_viewers:
                if init:
                    name = layer.name
                    data = layer.data
                    if insert:
                        layer_tmp = layers.Layer.create(data, {'name': name}, layer_type='labels')
                        view.layers.insert(index, layer_tmp)
                    else:
                        view.add_labels(data, name=name)
                view.layers[layer.name].data = layer.data
                view.layers[layer.name].selected_label = layer.selected_label
                view.layers[layer.name].opacity = layer.opacity
                view.layers[layer.name].brush_size = layer.brush_size
                view.layers[layer.name].blending = layer.blending
                view.layers[layer.name].colormap = layer.colormap
                view.layers[layer.name].contour = layer.contour
                view.layers[layer.name].n_edit_dimensions = layer.n_edit_dimensions
                view.layers[layer.name].contiguous = layer.contiguous
                view.layers[layer.name].preserve_labels = layer.preserve_labels
                view.layers[layer.name].show_selected_label = layer.show_selected_label
                view.layers[layer.name].visible = layer.visible

    def end_ortho(self):
        self.main_view.mouse_drag_callbacks.clear()
        self.main_view.mouse_wheel_callbacks.clear()
        self.layer_disconnect()
        self.main_view.layers.selection.events.changed.disconnect(self.layer_selection)
        self.main_view.layers.events.removed.disconnect(self.layer_removed)
        self.main_view.layers.events.inserted.disconnect(self.layer_inserted)
        self.main_view.layers.events.reordered.disconnect(self.layer_reordered)
        # disconnect zoom
        self.disconnect_zoom()
        # remove layers and viewers
        self.xz_view.layers.remove(self.xz_view.layers[self.viewfinder_xz.name])
        self.yz_view.layers.remove(self.yz_view.layers[self.viewfinder_yz.name])
        # Closing the viewers makes Napari menu crash, see https://github.com/napari/napari/issues/7588
        self.xz_view.close()
        self.yz_view.close()
        self.main_view.layers.remove(self.main_view.layers[self.viewfinder_xy.name])

    # currently unused methods

    # def mouse_double_click(self, viewer, event):
    #     # This will probably not be used
    #     print(event.position)
    #     print(self.x)


# TODO: refactor common utils?
def index_of_layer(viewer, layer):
    for i in range(len(viewer.layers)):
        if viewer.layers[i] == layer:
            return i
    # if not in list return false, useful for the widget
    return False
