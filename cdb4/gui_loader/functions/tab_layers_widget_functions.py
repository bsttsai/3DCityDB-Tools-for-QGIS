"""This module contains reset functions for each QT widgets.

The logic behind all of the functions is to reset widgets as individual
objects or as block of objects, depending on the needs.

The reset functions consist of clearing text or changed text to original state,
clearing widget items or selections and deactivating widgets.
"""
from ....cdb_tools_main import CDBToolsMain # Used only to add the type of the function parameters
from ...shared.functions import general_functions as gen_f
from .. import loader_constants as c
from . import canvas

FILE_LOCATION = gen_f.get_file_relative_path(file=__file__)

####################################################
## Setup widget functions for 'Layer' tab
####################################################

# In 'Basemap (OMS)' groupBox.
def gbxBasemapL_setup(cdbMain: CDBToolsMain) ->  None:
    """Function to setup the 'Basemap' groupbox. It uses an additional canvas instance to store an OSM map
    from which extents can be extracted for further spatial queries.
    The basemap is zoomed-in to the city model's extents (in 'Layers' tab)
    """
    dlg = cdbMain.loader_dlg

    # Set basemap of the layer tab.
    canvas.canvas_setup(cdbMain=cdbMain, canvas=dlg.CANVAS_L, extents=dlg.LAYER_EXTENTS, crs=dlg.CRS, clear=False)

    # Draw rubberband for extents of selected {cdb_schema}.
    canvas.insert_rubber_band(band=dlg.RUBBER_CDB_SCHEMA_L, extents=dlg.CDB_SCHEMA_EXTENTS, crs=dlg.CRS, width=3, color=c.CDB_EXTENTS_COLOUR)

    # Draw rubberband for extents of materialized views in selected {cdb_schema}.
    canvas.insert_rubber_band(band=dlg.RUBBER_LAYERS_L, extents=dlg.LAYER_EXTENTS, crs=dlg.CRS, width=2, color=c.LAYER_EXTENTS_COLOUR)

    # Zoom to the layer extents
    canvas.zoom_to_extents(canvas=dlg.CANVAS_L, extents=dlg.LAYER_EXTENTS)

    # Create polygon rubber band corresponding to the QGIS extents
    canvas.insert_rubber_band(band=dlg.RUBBER_QGIS_L, extents=dlg.CURRENT_EXTENTS, crs=dlg.CRS, width=1, color=c.QGIS_EXTENTS_COLOUR)

    return None


####################################################
## Reset widget functions for 'Layer' tab
####################################################

def tabLayers_reset(cdbMain: CDBToolsMain) -> None:
    """Function to reset the 'Import' tab.
    Resets: gbxAvailableL, gbxLayerSelection, gbxExtent and lblInfoText.
    """
    dlg = cdbMain.loader_dlg

    # Disable the tab
    dlg.tabLayers.setDisabled(True)
    # Reset all underlying objects
    lblInfoText_reset(cdbMain)
    gbxBasemapL_reset(cdbMain)
    gbxLayerSelection_reset(cdbMain)
    gbxAvailableL_reset(cdbMain)

    return None


def lblInfoText_reset(cdbMain: CDBToolsMain) -> None:
    """Function to reset the 'DB and Schema' label (in Layers tab).
    """
    dlg = cdbMain.loader_dlg

    dlg.lblInfoText.setText(dlg.lblInfoText.init_text)
    dlg.lblInfoText.setDisabled(True)

    return None


def gbxBasemapL_reset(cdbMain: CDBToolsMain) -> None:
    """Function to reset the 'Extents' groupbox (in Layers tab).
    """
    dlg = cdbMain.loader_dlg
    
    dlg.qgbxExtents.setDisabled(True)
    # Remove extent rubber bands.
    dlg.RUBBER_CDB_SCHEMA_L.reset()
    dlg.RUBBER_LAYERS_L.reset()
    dlg.RUBBER_QGIS_L.reset()

    return None


def gbxLayerSelection_reset(cdbMain: CDBToolsMain) -> None:
    """Function to reset the 'Parameters' group box (in Layers tab).
    """
    dlg = cdbMain.loader_dlg
    
    dlg.gbxLayerSelection.setDisabled(True)
    dlg.cbxFeatureType.clear()
    dlg.cbxLod.clear()

    return None


def gbxAvailableL_reset(cdbMain: CDBToolsMain) -> None:
    """Function to reset the 'Features to Import' group box (in Layers tab).
    """
    dlg = cdbMain.loader_dlg

    dlg.ccbxLayers.clear()
    dlg.gbxAvailableL.setDisabled(True)

    return None