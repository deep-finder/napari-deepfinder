
__version__ = "0.0.1"


from ._reader import napari_get_reader
from ._writer import write_annotations_xml
from ._widget import denoise_widget, reorder_widget, AddPointsWidget
from ._orthoview_widget import Orthoslice

# TODO: resolve the bugs that are causing the FutureWarnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
