Guide
=====

General purpose visualisation
-----------------------------

Open files
++++++++++

Once `napari-deepfinder` is installed, you will be able to open the files associated with the cryo-et workflow:

* tomograms and segmentation maps as `.mrc`, `.map`, `.rec`, `.h5`, `.tif` or `.TIF`
* annotation object lists as `.xml`, `.ods`, `.xls` or `.xlsx`

.. note:: The following features are all different widgets included in the plugin.

    To open them, click on the `Plugins` menu of napari, select napari-deepfinder` and you will see the list of widgets available.
    Click on the desired widget of this list to enable or disable it!

Automatic reordering of layers
++++++++++++++++++++++++++++++

A small widget has been added to reorder the layers automatically to have the tomograms at the bottom and superpose the segmentation map and the points annotations as a last layer.
Correctly ordered layers simplify the visualisation.

Orthoslice view (useful for annotation)
+++++++++++++++++++++++++++++++++++++++

Enable the `Orthoslice view` widget and activate the `Orthoslice` checkbox to start the orthoslice viewer.
You will now see 3 synchronised viewer (the main `x,y` viewer and 2 secondary `x, z` and `z, y` viewer).

.. important:: Please be careful and don't add widgets to the secondary viewers but only to the main viewer.

    This is currently a non-resolved technical issue, because e.g. on MacOS a user could in theory add a widget to secondary viewers.

Denoising (useful for annotation)
+++++++++++++++++++++++++++++++++++++++
The `Denoise tomogram` widget is for visualisation purposes only.
You can choose the image layer (tomogram) you want to denoise and the filter size (mean filter) you want to use.


Before-training phase (annotation)
----------------------------------

.. important:: The proper training of the neural network does not happen in this plugin

Annotation of points
++++++++++++++++++++
A basic `Annotation` widget is available, with some included information banner.
For each points annotation class, you need to create a points layer in napari and respect a naming convention that is explained inside the plugin.

This widget is designed for the orthoslice view and is not needed for annotation in non-orthoslice view
(but you need to respect the naming conventions explained in the widget information banner in non-orthoslice view nonetheless to be able to use the object list export function of the plugin!).

From the widget you can:
 * select a points layer
 * click on the desired position, in orthoslice view you will see the red viewfinder (red cross) move to that position
 * Click on `Add point` to add a point at that position.

Inference phase
---------------

.. important:: This phase is only possible once DeepFinder has been trained, training does not happen in this plugin.

Segmentation
++++++++++++
The `Segmentation` widget serves as a graphical user interface to generate a segmentation map based on the trained DeepFinder model.
You need to select the file containing the weights of the network and set other parameters.
Those parameters are mostly explained here: https://deepfinder.readthedocs.io/en/latest/guide.html#segmentation.

.. important:: Be aware that this step might last several minutes and consume a lot of RAM and computing ressources
    (you can play with the patch size to optimize the segmentation time:
    not too low to gain time, and not too high because it might lead in `out of memory (OOM)` errors because you don't have enough RAM).

Clustering
++++++++++
The `Clustering` widget enables to obtain the points/the centroids of some macromolecules based on the segmentation map.

.. important:: It is strongly recommended to perform this step on a binned segmentation map.

    So at the previous step select `Bin label map`.
    Do not use the segmentation map visible in you viewer, but reload the saved binned label map from the saved file.

For more information about this step and the several parameters, you can have a look here: https://deepfinder.readthedocs.io/en/latest/guide.html#clustering.