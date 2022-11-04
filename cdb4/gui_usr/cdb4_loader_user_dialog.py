# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DBLoaderDialog
                                 A QGIS plugin
                This is a plugin for the CityGML 3D City Database.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-09-30
        git sha              : $Format:%H$
        author(s)            : Konstantinos Pantelios
                               Giorgio Agugiaro
        email                : konstantinospantelios@yahoo.com
                               g.agugiaro@tudelft.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import (
    Qgis,
    QgsMessageLog,
    QgsProject,
    QgsRectangle, 
    QgsGeometry)
from qgis.PyQt import (
    uic,
    QtWidgets)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox 

import os

from ...cdb_loader import CDBLoader # Used only to add the type of the function parameters

from ..gui_db_connector.db_connection_dialog import DBConnectorDialog
from ..gui_db_connector.functions import conn_functions as conn_f

from ... import main_constants as main_c
from .. import cdb4_constants as c

from .functions import tab_conn_widget_functions as ct_wf
from .functions import tab_conn_functions as uc_tf

from .functions import tab_layers_widget_functions as lt_wf
from .functions import tab_layers_functions as l_tf

from .functions import canvas, sql, threads as thr

# This loads the .ui file so that PyQt can populate the plugin
# with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), "ui", "cdb4_loader_user_dialog.ui"))

class CDB4LoaderUserDialog(QtWidgets.QDialog, FORM_CLASS):
    """User Dialog class of the plugin.
    The GUI is imported from an external .ui xml
    """

    def __init__(self, cdbLoader: CDBLoader, parent=None):
        """Constructor."""
        super(CDB4LoaderUserDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # Enhance various Qt Objects with their initial text.
        # This is used in order to revert to the original state
        # in reset operations when original text has already changed.
        self.btnConnectToDbC.init_text = c.btnConnectToDbC_t
        self.btnCreateLayers.init_text = c.btnCreateLayers_t
        self.btnRefreshLayers.init_text = c.btnRefreshLayers_t
        self.btnDropLayers.init_text = c.btnDropLayers_t
        self.btnCityExtentsC.init_text = c.btnCityExtentsC_t
        self.lblInfoText.init_text = c.lblInfoText_t
        self.btnCityExtents.init_text = c.btnCityExtents_t
        self.ccbxFeatures.init_text = c.ccbxFeatures_t

        ### SIGNALS (start) ############################

        #### 'User Connection' tab

        # 'Connection' group box signals
        self.cbxExistingConnC.currentIndexChanged.connect(lambda: self.evt_cbxExistingConn_changed(cdbLoader))
        
        #self.btnNewConnC.clicked.connect(self.evt_btnNewConn_clicked)
        self.btnNewConnC.clicked.connect(lambda: self.evt_btnNewConn_clicked(cdbLoader))

        # 'Database' group box signals
        self.btnConnectToDbC.clicked.connect(lambda: self.evt_btnConnectToDb_clicked(cdbLoader))
        self.cbxSchema.currentIndexChanged.connect(lambda: self.evt_cbxSchema_changed(cdbLoader))

        # Basemap (OSM) group box signals
        # Link the addition canvas to the extents qgroupbox and
        # enable "MapCanvasExtent" options (Byproduct).
        self.qgbxExtentsC.setMapCanvas(canvas=cdbLoader.CANVAS_C, drawOnCanvasOption = False)

        # Draw on Canvas tool is disabled.
        # Check Note on main>widget_setup>ws_layers_tab.py>qgbxExtents_setup
        self.qgbxExtentsC.setOutputCrs(outputCrs=cdbLoader.CRS)

        # 'Extents' groupbox signals
        self.btnCityExtentsC.clicked.connect(lambda: self.evt_btnCityExtentsC_clicked(cdbLoader))
        cdbLoader.CANVAS_C.extentsChanged.connect(lambda: self.evt_canvas_ext_changed(cdbLoader))
        self.qgbxExtentsC.extentChanged.connect(lambda: self.evt_qgbxExtentsC_ext_changed(cdbLoader))

        self.btnCreateLayers.clicked.connect(lambda: self.evt_btnCreateLayers_clicked(cdbLoader))
        self.btnRefreshLayers.clicked.connect(lambda: self.evt_btnRefreshLayers_clicked(cdbLoader))
        self.btnDropLayers.clicked.connect(lambda: self.evt_btnDropLayers_clicked(cdbLoader))

        self.btnCloseConnC.clicked.connect(lambda: self.evt_btnCloseConnC_clicked(cdbLoader))

        #### 'Layer ' tab
        
        #Link the addition canvas to the extents qgroupbox and
        #enable "MapCanvasExtent" options (Byproduct).
        self.qgbxExtents.setMapCanvas(canvas=cdbLoader.CANVAS, drawOnCanvasOption=False)
        #Draw on Canvas tool is disabled.
        #Check Note on main>widget_setup>ws_layers_tab.py>qgbxExtents_setup
        self.qgbxExtents.setOutputCrs(outputCrs=cdbLoader.CRS)

        # 'Extents' groupbox signals (in 'Layers' tab)
        self.qgbxExtents.extentChanged.connect(lambda: self.evt_qgbxExtents_extChanged(cdbLoader))
        self.btnCityExtents.clicked.connect(lambda: self.evt_btnCityExtents_clicked(cdbLoader))          

        # 'Parameters' groupbox signals (in 'Layers' tab)
        self.cbxFeatureType.currentIndexChanged.connect(lambda: self.evt_cbxFeatureType_changed(cdbLoader))
        self.cbxLod.currentIndexChanged.connect(lambda: self.evt_cbxLod_changed(cdbLoader))

        # 'Features to Import' groupbox signals (in 'Layers' tab)
        self.ccbxFeatures.checkedItemsChanged.connect(lambda: self.evt_cbxFeatures_changed(cdbLoader))
        self.btnImport.clicked.connect(lambda: self.evt_btnImport_clicked(cdbLoader))

        ### SIGNALS (end) ############################


    ### EVENTS (start) ############################

    ## Events for 'User connection' tab BEGIN

    #'Connection' group box events (in 'User Connection' tab)
    def evt_cbxExistingConn_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Existing Connection'
        comboBox (cbxExistingConnC) current index changes.
        This function runs every time the current selection of 
        'Existing Connection' changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Set the current database connection object variable
        cdbLoader.DB = self.cbxExistingConnC.currentData()
        if not cdbLoader.DB:
            return None

        # Reset the tabs
        ct_wf.tabConnection_reset(cdbLoader)
        lt_wf.tabLayers_reset(cdbLoader)

        # Reset and (re)enable the "3D City Database" connection box and buttons
        dlg.gbxDatabase.setDisabled(False)   # Activate the group box
        dlg.btnConnectToDbC.setText(dlg.btnConnectToDbC.init_text.format(db=cdbLoader.DB.database_name))  # set the label
        dlg.btnConnectToDbC.setDisabled(False)  # Activate the button 
        dlg.lblConnectToDB.setDisabled(False)   # Activate the label

        # Close the current open connection.
        if cdbLoader.conn is not None:
            cdbLoader.conn.close()


    def evt_btnNewConn_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'New Connection' pushButton
        (btnNewConnC) is pressed.

        Responsible to add a new VALID connection to the 'Existing connections'.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Create/Show/Execute additional dialog for the new connection
        dlgConnector = DBConnectorDialog()
        dlgConnector.setWindowModality(2)
        dlgConnector.show()
        dlgConnector.exec_()

        # Add new connection to the Existing connections
        if dlgConnector.new_connection:
            dlg.cbxExistingConnC.addItem(f"{dlgConnector.new_connection.connection_name}",dlgConnector.new_connection)
                #dlgConnector.close()

    # 'Database' group box events (in 'User Connection' tab)
    def evt_btnConnectToDb_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the current 'Connect to {db}' pushButton
        (btnConnectToDbC) is pressed.
        It sets up the GUI after a click signal is emitted.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        #In 'Connection Status' groupbox
        dlg.gbxConnStatusC.setDisabled(False) # Activate the connection status box (red/green checks)
        dlg.btnCloseConnC.setDisabled(False) # Activate the close connection button at the bottom

        # Attempt to connect to the database, returns True/False
        successful_connection = conn_f.open_connection(cdbLoader)

        if successful_connection:
            # Show database name
            dlg.lblConnToDbC_out.setText(c.success_html.format(text=cdbLoader.DB.database_name))
            cdbLoader.DB.green_db_conn = True

            if cdbLoader.DB.pg_server_version is not None:
                # Show server version
                dlg.lblPostInstC_out.setText(c.success_html.format(text=cdbLoader.DB.pg_server_version))
                cdbLoader.DB.green_postgis_inst = True
            else:
                dlg.lblPostInstC_out.setText(c.failure_html.format(text=c.PG_SERVER_FAIL_MSG))
                cdbLoader.DB.green_post_inst = False
                return None

            # Rework the series of tests to be carried out, most of them are relevant only during installation as admin.
            #
            # 1) Can I connect to the database?
            # 2) Is my qgis_user schema installed? If yes, continue.
            # 3) Am I connecting to a version of the QGIS package that is compatible with this version of the plugin? If yes, continue
            #        This implies that PostGIS and the 3DCityDB are there and also correct. No need to check, actually.
            #        Therefore, optionally, show server, postgis and citydb version (might be removed in future)
            # 4) Are there cdb_schemas I am allowed to connect to? If yes, continue
            # 5) Can I connect to at least one non-empty cdb_schema?
            #       - If yes, continue

            # Create and set schema name for user in cdbLoader.USR_SCHEMA
            sql.exec_create_qgis_usr_schema_name(cdbLoader)

            # Check if user package (usr_schema, e.g. qgis_giorgio) is installed in the database.
            has_user_inst = sql.is_usr_pkg_installed(cdbLoader)
            if has_user_inst:
                # Get the current qgis_pkg version.
                qgis_pkg_curr_version = sql.exec_qgis_pkg_version(cdbLoader)  # returns a tuple
                qgis_pkg_curr_version_txt = qgis_pkg_curr_version[0]
                qgis_pkg_curr_version_major = qgis_pkg_curr_version[2]
                qgis_pkg_curr_version_minor = qgis_pkg_curr_version[3]
                qgis_pkg_curr_version_minor_rev = qgis_pkg_curr_version[4]

                # Check that the QGIS Package version is >= than the minimum required for this versin of the plugin (see cdb4_constants.py)
                if (qgis_pkg_curr_version_major >= c.QGIS_PKG_MIN_VERSION_MAJOR) and \
                   (qgis_pkg_curr_version_minor >= c.QGIS_PKG_MIN_VERSION_MINOR) and \
                   (qgis_pkg_curr_version_minor_rev >= c.QGIS_PKG_MIN_VERSION_MINOR_REV):

                    # Show message in Connection Status the Qgis Package is installed (and version)
                    dlg.lblMainInstC_out.setText(c.success_html.format(text=" ".join([c.INST_MSG, f"(v.{qgis_pkg_curr_version_txt})"]).format(pkg=main_c.QGIS_PKG_SCHEMA)))
                    cdbLoader.DB.green_main_inst = True
                else:
                    dlg.lblMainInstC_out.setText(c.failure_html.format(text=c.INST_FAIL_VERSION_MSG))
                    cdbLoader.DB.green_main_inst = False
                    QgsMessageLog.logMessage(f"The current version of the QGIS Package installed in this database is {qgis_pkg_curr_version_txt} and is not supported anymore. Please contact your database administrator and update to version {c.QGIS_PKG_MIN_VERSION_TXT} (or higher).",
                                            "3DCityDB-Loader", level=Qgis.Critical)
                    QMessageBox.warning(dlg, "Unsupported version of QGIS Package", 
                                            f"The current version of the QGIS Package installed in this database is {qgis_pkg_curr_version_txt} and is not supported anymore.\nPlease contact your database administrator and update to version {c.QGIS_PKG_MIN_VERSION_TXT} (or higher).")
                    return None

                # Show message in Connection Status the 3DCityDB version if installed
                cdbLoader.DB.citydb_version = sql.fetch_3dcitydb_version(cdbLoader)
                dlg.lbl3DCityDBInstC_out.setText(c.success_html.format(text=cdbLoader.DB.citydb_version))
                cdbLoader.DB.green_citydb_inst = True

                # Show message in Connection Status that the Qgis user schema is installed               
                dlg.lblUserInstC_out.setText(c.success_html.format(text=c.INST_MSG.format(pkg=cdbLoader.USR_SCHEMA)))
                cdbLoader.DB.green_user_inst = True

                # Get the list of 3DCityDB schemas from database as a tuple. If empty, len(tuple)=0
                schema_names_tot, schema_nums_tot = sql.exec_list_cdb_schemas_all(cdbLoader)

                # Create tuples containing only non-empty cdb_schemas
                schema_names = list()
                schema_nums = list()
                for i in range(len(schema_names_tot)):
                    if schema_nums_tot[i] != 0:
                        schema_names.append(schema_names_tot[i])
                        schema_nums.append(schema_nums_tot[i])
                schema_names = tuple(schema_names)
                schema_nums = tuple(schema_nums)
   
                if len(schema_names_tot) == 0: # Inform the use that there are no cdb schemas to be chosen from.
                    QMessageBox.warning(dlg, "No accessible citydb schemas found", "No citydb schemas could be retrieved from the database. You may lack proper privileges to access them. Please contact your database administrator.")
                    return None
                else:
                    if len(schema_names) == 0:
                        # Inform the use that all available cdb schemas are empty.
                        QMessageBox.warning(dlg, "Empty citydb schema(s)", "The available citydb schema(s) is/are all empty. Please load data into the database first.")
                        return None
                    else: # Finally, we have all conditions to fill the cdb_schema combobox
                        uc_tf.fill_schema_box(cdbLoader, schemas=schema_names)
                        # At this point, filling the schema box, activates the 'evt_cbxSchema_changed' event.
                        # So if you're following the code line by line, go to citydb_loader.py>evt_cbxSchema_changed or at 'cbxSchema_setup' function below
            else:
                dlg.lblUserInstC_out.setText(c.failure_html.format(text=c.INST_FAIL_MSG.format(pkg=f"qgis_{cdbLoader.DB.username}")))
                cdbLoader.DB.green_user_inst = False
                QgsMessageLog.logMessage(f"The required user schema 'qgis_{cdbLoader.DB.username}' is missing. Please contact your database administrator to install it",
                                        "3DCityDB-Loader", level=Qgis.Critical)
                QMessageBox.warning(dlg, "User schema not found", f"The required user schema 'qgis_{cdbLoader.DB.username}' is missing. Please contact your database administrator to install it")
                return None
        else: # Connection failed!
            ct_wf.gbxConnStatus_reset(cdbLoader)
            dlg.gbxConnStatusC.setDisabled(False)
            dlg.lblConnToDbC_out.setText(c.failure_html.format(text=c.CONN_FAIL_MSG))
            cdbLoader.DB.green_connection = False
            dlg.lblPostInstC_out.setText(c.failure_html.format(text=c.PG_SERVER_FAIL_MSG))
            cdbLoader.DB.green_pg_server_version = False
            return None

        return None

    def evt_cbxSchema_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'schemas' comboBox (cbxSchema)
        current index changes.
        Function to setup the GUI after an 'indexChanged' signal is emitted from
        the cbxSchema combo box.
        This function runs every time the selected schema is changed.
        (in 'User Connection' tab)
        Checks if the connection + schema meet the necessary requirements.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Set the current schema variable
        cdbLoader.CDB_SCHEMA = dlg.cbxSchema.currentText()
        # By now, the schema variable must have be assigned.
        if not dlg.cbxSchema.currentData():
            return None

        # Enable schema comboBox
        dlg.cbxSchema.setDisabled(False)
        dlg.lblSchema.setDisabled(False)

        # Clear status of previous schema.
        dlg.lblLayerExist_out.clear()
        dlg.lblLayerRefr_out.clear()

        dlg.btnCityExtentsC.setText(dlg.btnCityExtentsC.init_text.format(sch=cdbLoader.CDB_SCHEMA))
        dlg.btnRefreshLayers.setText(dlg.btnRefreshLayers.init_text.format(sch=cdbLoader.CDB_SCHEMA))
        dlg.btnCreateLayers.setText(dlg.btnCreateLayers.init_text.format(sch=cdbLoader.CDB_SCHEMA))
        dlg.btnDropLayers.setText(dlg.btnDropLayers.init_text.format(sch=cdbLoader.CDB_SCHEMA))

        dlg.gbxBasemapC.setDisabled(False)
        dlg.cgbxOptions.setDisabled(False)        
        dlg.btnCreateLayers.setDisabled(False)

        # Setup the 'Basemap (OSM)' groupbox.
        ct_wf.gbxBasemapC_setup(cdbLoader, cdbLoader.CANVAS_C)

        mview_exts = sql.fetch_extents(cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, ext_type=c.MAT_VIEW_EXT_TYPE)
        if mview_exts:
            # Put extents coordinates into the widget. Singal emitted for qgbxExtentsC.
            dlg.qgbxExtentsC.setOutputExtentFromUser(QgsRectangle.fromWkt(mview_exts), cdbLoader.CRS)

        # Check if user package has views corresponding to the current schema (layers).
        has_layers_in_current_schema = sql.exec_has_layers_for_cdbschema(cdbLoader)
        if has_layers_in_current_schema:
            dlg.lblLayerExist_out.setText(c.success_html.format(text=c.SCHEMA_LAYER_MSG.format(sch=cdbLoader.CDB_SCHEMA)))
            cdbLoader.DB.green_schema_supp = True

            dlg.btnRefreshLayers.setDisabled(False)
            dlg.btnDropLayers.setDisabled(False)        
        else:
            dlg.lblLayerExist_out.setText(c.failure_html.format(text=c.SCHEMA_LAYER_FAIL_MSG.format(sch=cdbLoader.CDB_SCHEMA)))
            cdbLoader.DB.green_schema_supp = False
            return None

        # Check if the materialised views are populated.
        refresh_date = sql.fetch_layer_metadata(cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, cols="refresh_date")
        # Extract a date.
        date = list(set(refresh_date[1]))[0][0]
        if date:
            dlg.lblLayerRefr_out.setText(c.success_html.format(text=c.REFR_LAYERS_MSG.format(date=date)))
            cdbLoader.DB.green_refresh_date = True
        else:
            dlg.lblLayerRefr_out.setText(c.failure_html.format(text=c.REFR_LAYERS_FAIL_MSG))
            cdbLoader.DB.green_refresh_date = False
            return None

        # Check that DB is configured correctly. If so, enable all following buttons etc.
        if cdbLoader.DB.user_meets_requirements():
            dlg.tabLayers.setDisabled(False)
            dlg.lblInfoText.setDisabled(False)
            dlg.lblInfoText.setText(dlg.lblInfoText.init_text.format(
                        db=cdbLoader.DB.database_name,
                        usr=cdbLoader.DB.username,
                        sch=cdbLoader.CDB_SCHEMA))
            dlg.gbxBasemap.setDisabled(False)
            dlg.qgbxExtents.setDisabled(False)
            dlg.btnCityExtents.setDisabled(False)
            dlg.btnCityExtents.setText(dlg.btnCityExtents.init_text.format(sch="layers extents"))
        
            lt_wf.gbxBasemap_setup(cdbLoader, cdbLoader.CANVAS)

            dlg.tabLayers.setDisabled(False)           

            # We are done here with the 'User Connection' tab.

        else:
            lt_wf.tabLayers_reset(cdbLoader)
            dlg.tabLayers.setDisabled(True)

    # 'Basemap (OSM)' group box events (in 'User Connection' tab)
    def evt_canvas_ext_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the current canvas extents (pan over map)
        changes.

        Reads the new current extents from the map and sets it in the 'Extents'
        (qgbxExtentsC) widget.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Get canvas's current extent
        extent: QgsRectangle = cdbLoader.CANVAS_C.extent()

        # Set the current extent to show in the 'extent' widget.
        dlg.qgbxExtentsC.setCurrentExtent(currentExtent=extent, currentCrs=cdbLoader.CRS)
        dlg.qgbxExtentsC.setOutputCrs(outputCrs=cdbLoader.CRS)


    def evt_qgbxExtentsC_ext_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Extents' groubBox (qgbxExtentsC)
        extent in widget changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Update extents variable with the ones that fired the signal.
        cdbLoader.CURRENT_EXTENTS = dlg.qgbxExtentsC.outputExtent()
        if cdbLoader.CURRENT_EXTENTS.isNull() or cdbLoader.CDB_SCHEMA_EXTENTS.isNull():
            return None

        # Draw the extents in the additional canvas (basemap)
        canvas.insert_rubber_band(
            band=cdbLoader.RUBBER_LAYERS_C,
            extents=cdbLoader.CURRENT_EXTENTS,
            crs=cdbLoader.CRS,
            width=2,
            color=Qt.red)

        # Compare original extents with user defined ones.
        layer_exts = QgsGeometry.fromRect(cdbLoader.CURRENT_EXTENTS)
        cdb_exts = QgsGeometry.fromRect(cdbLoader.CDB_SCHEMA_EXTENTS)

        # Check validity of user extents relative to the City Model's extents.
        if not layer_exts.intersects(cdb_exts):
            QMessageBox.critical(
                cdbLoader.usr_dlg,
                "Warning",
                f"Pick a region inside the extents of '{cdbLoader.CDB_SCHEMA}' (blue area).")
            return None
        else:
            cdbLoader.LAYER_EXTENTS = cdbLoader.CURRENT_EXTENTS


    def evt_btnCityExtentsC_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the current 'Calculate from City model'
        pushButton (btnCityExtentsC) is pressed.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Get the extents stored in server (already computed at this point).
        extents = sql.fetch_extents(
            cdbLoader,
            usr_schema=cdbLoader.USR_SCHEMA,
            cdb_schema=cdbLoader.CDB_SCHEMA,
            ext_type=c.CDB_SCHEMA_EXT_TYPE)
        assert extents, "Extents don't exist but should have been already computed!"

        # Convert extents format to QgsRectangle object.
        extents = QgsRectangle.fromWkt(extents)
        # Update extents in plugin variable.
        cdbLoader.CURRENT_EXTENTS = extents

        # Put extents coordinates into the widget.
        dlg.qgbxExtentsC.setOutputExtentFromUser(cdbLoader.CURRENT_EXTENTS, cdbLoader.CRS)
        # At this point an extentChanged signal is emitted.
        
        # Zoom to these extents.
        cdbLoader.CANVAS_C.zoomToFeatureExtent(extents)


    def evt_btnCreateLayers_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Create layers for schema {sch}'
        pushButton (btnCreateLayers) is pressed.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        thr.create_layers_thread(cdbLoader)

        # Update the layer extents in the corresponding table in the server.
        sql.exec_upsert_extents(
            cdbLoader,
            usr_schema=cdbLoader.USR_SCHEMA,
            cdb_schema=cdbLoader.CDB_SCHEMA,
            bbox_type=c.MAT_VIEW_EXT_TYPE,
            extents=cdbLoader.LAYER_EXTENTS.asWktPolygon())

        refresh_date = []
        while not refresh_date: # Loop to allow for 'layer creation' thread to finish. It seems hacky...
            # Check if the materialised views are populated. # NOTE: Duplicate code!
            refresh_date = sql.fetch_layer_metadata(
                    cdbLoader, 
                    usr_schema=cdbLoader.USR_SCHEMA, 
                    cdb_schema=cdbLoader.CDB_SCHEMA,
                    cols="refresh_date")
            # Extract a date.
            refresh_date = list(set(refresh_date[1]))

        date = refresh_date[0][0] # Extract date.
        if date:
            dlg.lblLayerRefr_out.setText(c.success_html.format(text=c.REFR_LAYERS_MSG.format(date=date)))
            cdbLoader.DB.green_refresh_date = True
        else:
            dlg.lblLayerRefr_out.setText(c.failure_html.format(text=c.REFR_LAYERS_FAIL_MSG))
            cdbLoader.DB.green_refresh_date = False
            return None


    def evt_btnRefreshLayers_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Refresh layers for schema {sch}'
        pushButton (btnRefreshLayers) is pressed.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        res = QMessageBox.question(dlg, "Layer refresh", c.REFRESH_QUERY)
        if res == 16384: #YES
            thr.refresh_views_thread(cdbLoader)


    def evt_btnDropLayers_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Drop layers for schema {sch}'
        pushButton (btnRefreshLayers) is pressed.
        """
        thr.drop_layers_thread(cdbLoader)


    def evt_btnCloseConnC_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Close current connection' pushButton
        (btnCloseConn) is pressed.
        """
        ct_wf.tabConnection_reset(cdbLoader)
        lt_wf.tabLayers_reset(cdbLoader)

    ## Events for User connection tab END

    ## Events for Layer tab BEGIN

    # 'Parameters' group box events (in 'Layers' tab)
    def evt_qgbxExtents_extChanged(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Extents' groubBox (qgbxExtents)
        extent changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # NOTE: 'Draw on Canvas'* has an undesired effect.
        # There is a hardcoded True value that causes the parent dialog to
        # toggle its visibility to let the user draw. But in our case
        # the parent dialog contains the canvas that we need to draw on.
        # Re-opening the plugin allows us to draw in the canvas but with the
        # caveat that the drawing tool never closes (also causes some QGIS crashes).
        # https://github.com/qgis/QGIS/blob/master/src/gui/qgsextentgroupbox.cpp
        # https://github.com/qgis/QGIS/blob/master/src/gui/qgsextentwidget.h
        # line 251 extentDrawn function
        # https://qgis.org/pyqgis/3.16/gui/QgsExtentGroupBox.html
        # https://qgis.org/pyqgis/3.16/gui/QgsExtentWidget.html

        # Update extents variable with the ones that fired the signal.
        cdbLoader.CURRENT_EXTENTS = dlg.qgbxExtents.outputExtent()

        # Draw the extents in the addtional canvas (basemap)
        canvas.insert_rubber_band(
            band=cdbLoader.RUBBER_USER,
            extents=cdbLoader.CURRENT_EXTENTS,
            crs=cdbLoader.CRS,
            width=2,
            color=Qt.green)

        # Compare original extents with user defined ones.
        qgis_exts = QgsGeometry.fromRect(cdbLoader.CURRENT_EXTENTS)
        layer_exts = QgsGeometry.fromRect(cdbLoader.LAYER_EXTENTS)

        # Check validity of user extents relative to the City Model's extents.
        if layer_exts.equals(qgis_exts) or layer_exts.intersects(qgis_exts):
            cdbLoader.QGIS_EXTENTS = cdbLoader.CURRENT_EXTENTS
        elif qgis_exts.equals(QgsGeometry.fromRect(QgsRectangle(0,0,0,0))):
            # When the basemap is initialized (the first time),
            # the current extents are 0,0,0,0 and are compared against the extents 
            # of the layers which are coming from the DB.
            # This causes the "else" to pass which we don't want.  
            #NOTE: this solution is temporary KP 01/09/22
            pass 
        else:
            QMessageBox.critical(dlg, "Warning", f"Pick a region inside the layers extents (red area).")          
            return None

        lt_wf.gbxLayerSelection_reset(cdbLoader)
        dlg.gbxLayerSelection.setDisabled(False)
        
        # Operations cascade to a lot of functions from here!
        # Based on the selected extents fill out the Feature Types combo box.
        l_tf.fill_FeatureType_box(cdbLoader)

        return None


    def evt_btnCityExtents_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the current 'Set to layers extents'
        pushButton (btnCityExtents) is pressed.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Get the extents stored in server (already computed at this point).
        extents = sql.fetch_extents(
            cdbLoader,
            usr_schema=cdbLoader.USR_SCHEMA,
            cdb_schema=cdbLoader.CDB_SCHEMA,
            ext_type=c.MAT_VIEW_EXT_TYPE)
        assert extents, "Extents don't exist but should have been already computed!"

        # Convert extents format to QgsRectangle object.
        extents = QgsRectangle.fromWkt(extents)
        # Update extents in plugin variable.
        cdbLoader.CURRENT_EXTENTS = extents
        cdbLoader.QGIS_EXTENTS = extents

        # Put extents coordinates into the widget.
        dlg.qgbxExtents.setOutputExtentFromUser(cdbLoader.CURRENT_EXTENTS, cdbLoader.CRS)
        # At this point an extentChanged signal is emitted.

        # Zoom to these extents.
        cdbLoader.CANVAS.zoomToFeatureExtent(extents)


    def evt_cbxFeatureType_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Feature Type'comboBox (cbxFeatureType)
        current index changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Clear 'Geometry Level' combo box from previous runs.
        dlg.cbxLod.clear()

        # Enable 'Geometry Level' combo box
        dlg.cbxLod.setDisabled(False)

        # Fill out the LoDs, based on the selected extents and Feature Type.
        l_tf.fill_lod_box(cdbLoader)


    def evt_cbxLod_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Geometry Level'comboBox (cbxLod)
        current index changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Enable 'Features to Import' group box.
        dlg.gbxAvailableL.setDisabled(False)

        # Clear 'Features' checkable combo box from previous runs.
        dlg.ccbxFeatures.clear()

        # Revert to initial text.
        dlg.ccbxFeatures.setDefaultText(dlg.ccbxFeatures.init_text)

        # Fill out the features.
        l_tf.fill_features_box(cdbLoader)


    # 'Features to Import' group box events (in 'Layers' tab)
    def evt_cbxFeatures_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Available Features'
        checkableComboBox (ccbxFeatures) current index changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg

        # Get all the selected layers (views).
        checked_views = dlg.ccbxFeatures.checkedItems()

        if checked_views:
            # Enable 'Import' pushbutton.
            dlg.btnImport.setDisabled(False)
        else:
            # Revert to initial text and disable 'Import' pushbutton
            dlg.btnImport.setDisabled(True)


    def evt_btnImport_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Import Features' pushButton
        (btnImport) is pressed.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.usr_dlg
        
        # Get the data that is checked from 'ccbxFeatures'
        # Remember widget hold items in the form of (view_name, View_object)
        checked_views = l_tf.get_checkedItemsData(dlg.ccbxFeatures)

        #checked_views = dlg.ccbxFeatures.checkedItemsData()
        # NOTE: this built-in method works only for string types. 
        # Check https://qgis.org/api/qgscheckablecombobox_8cpp_source.html line 173

        # Get the total number of features to be imported.
        counter = 0
        for view in checked_views:
            counter += view.n_selected

        # Warn user when too many features are to be imported.
        if counter>c.MAX_FEATURES_PER_LAYER:
            res = QMessageBox.question(dlg, "Warning", f"Many features ({counter}) within the selected area!\nThis could reduce QGIS performance and may lead to crashes.\nDo you want to continue anyway?")
            if res == 16384: # YES, proceed with importing layers
                success = l_tf.import_layers(cdbLoader, layers=checked_views)
            else:
                return None #Import Cancelled
        else:
            success = l_tf.import_layers(cdbLoader, layers=checked_views)

        if not success:
            QgsMessageLog.logMessage(
                message="Something went wrong while importing the layer(s)!",
                tag=main_c.PLUGIN_NAME,
                level=Qgis.Critical,
                notifyUser=True)
            return None


        # Structure 'Table of Contents' tree.
        db_group = l_tf.get_node_database(cdbLoader)
        l_tf.sort_ToC(db_group)
        l_tf.send_to_top_ToC(db_group)

        # Finally bring the Relief Feature type at the bottom of the ToC.
        l_tf.send_to_bottom_ToC(QgsProject.instance().layerTreeRoot())

        # Set CRS of the project to match the one of the 3DCityDB.
        QgsProject.instance().setCrs(cdbLoader.CRS)
        
        # A final success message.
        QgsMessageLog.logMessage(
                message="",
                tag=main_c.PLUGIN_NAME,
                level=Qgis.Success,
                notifyUser=True)
        return None

        # Here is the final step.
        # Meaning that user did everything and can now close
        # the window to continue working outside the plugin.


#NOTE: extent groupbox doesn't work for manual user input
#for every value change in any of the 4 inputs the extent signal is emitted

    ## Events for Layer tab END

    ### EVENTS (end) ############################