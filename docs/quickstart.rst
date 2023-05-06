Quickstart
==========

A clean environment
-------------------

First of all you need a working installation of napari, you can refer to that webpage for more info https://napari.org/#installation .

It is strongly recommended to work with virtual environments (such as virtualenv or conda).
You can create a new environment especially for your work with `napari-deepfinder`.
This is really useful and advised, especially because `napari-deepfinder` will install a lot of dependencies (including deepfinder and it's dependencies).

Installation of `napari-deepfinder`
-----------------------------------

The general purpose guide for installing napari plugins is available `here <https://napari.org/plugins/find_and_install_plugin.html>`_.

Basically you need to start napari and go in the plugin menu. There you will find the `Install/Uninstall Plugins` entry, which once clicked opens a new dedicated window.
There you can either:

 * Enter the name `napari-deepfinder`
 * Enter the url https://github.com/deep-finder/napari-deepfinder
 * Drag and drop the folder of a downloaded copy of the source code of the plugin

.. raw:: html

   <details>
   <summary><a>Command line installation for more advanced users</a></summary>

You can also install the plugin through the command line in the virtual environment by using `pip <https://pypi.org/project/pip/>`_:
    ``pip install napari-deepfinder``
or (for the latest development version):
    ``pip install git+https://github.com/deep-finder/napari-deepfinder.git``

.. raw:: html

   </details>
