__version__ = "0.0.1"


# TODO: resolve the bugs that are causing the FutureWarnings
import warnings

from ._orthoview_widget import Orthoslice
from ._reader import napari_get_reader
from ._widget import AddPointsWidget, denoise_widget, reorder_widget
from ._writer import write_annotations_xml

warnings.simplefilter(action="ignore", category=FutureWarning)

__all__ = (
    "napari_get_reader",
    "write_annotations_xml",
    "denoise_widget",
    "reorder_widget",
    "AddPointsWidget",
    "Orthoslice",
)
