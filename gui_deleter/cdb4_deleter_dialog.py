# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CDB4DeleterDialog
                                 A QGIS plugin
                This is a plugin for the CityGML 3D City Database.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-12-15
        git sha              : $Format:%H$
        author(s)            : Tendai Mbwanda
                               Giorgio Agugiaro
        email                : t.mbwanda@student.tudelft.nl
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
from qgis.core import Qgis, QgsMessageLog, QgsRectangle, QgsGeometry, QgsWkbTypes, QgsCoordinateReferenceSystem
from qgis.gui import QgsRubberBand, QgsMapCanvas
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox
import os
import psycopg2

from ...cdb_loader import CDBLoader # Used only to add the type of the function parameters
from .other_classes import DeleterDialogRequirements, DeleterDialogSettings

from ..gui_db_connector.other_classes import Connection # Used only to add the type of the function parameters
from ..gui_db_connector.new_db_connection_dialog import DBConnectorDialog
from ..gui_db_connector.functions import conn_functions as conn_f

from .. import cdb4_constants as c

from .functions import tab_conn_widget_functions as ct_wf
from .functions import tab_conn_functions as uc_tf


from .functions import canvas, sql, threads as thr
from ..shared.functions import sql as sh_sql

# This loads the .ui file so that PyQt can populate the plugin
# with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "cdb4_deleter_dialog.ui"))

class CDB4DeleterDialog(QtWidgets.QDialog, FORM_CLASS):
    """User Dialog class of the plugin. The GUI is imported from an external .ui xml
    """

    def __init__(self, cdbLoader: CDBLoader, parent=None):
        """Constructor."""
        super(CDB4DeleterDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html#widgets-and-dialogs-with-auto-connect

        self.setupUi(self)

        ############################################################
        ## From here you can add your variables or constants
        ############################################################

        self.requirements = DeleterDialogRequirements()
        #print(self.requirements)

        self.settings = DeleterDialogSettings()
        #print(self.settings)

        # Variable to store the selected crs.
        self.CRS: QgsCoordinateReferenceSystem = cdbLoader.iface.mapCanvas().mapSettings().destinationCrs()

        # Variable to store the selected extents.
        self.CURRENT_EXTENTS: QgsRectangle = cdbLoader.iface.mapCanvas().extent()
        # Variable to store the extents of the selected cdb_schema
        self.CDB_SCHEMA_EXTENTS_BLUE: QgsRectangle = cdbLoader.iface.mapCanvas().extent()
        # Variable to store the extents of the Layers
        self.LAYER_EXTENTS_RED: QgsRectangle = cdbLoader.iface.mapCanvas().extent()
        # Variable to store the extents of the QGIS layers.
        self.QGIS_EXTENTS_GREEN: QgsRectangle = cdbLoader.iface.mapCanvas().extent()

        # Variable to store an additional canvas (to show the extents in the CONNECTION TAB).
        self.CANVAS_C: QgsMapCanvas = QgsMapCanvas()
        self.CANVAS_C.enableAntiAliasing(True)
        self.CANVAS_C.setMinimumWidth(300)
        self.CANVAS_C.setMaximumHeight(350)

        # Variable to store a rubberband formed by the current extents.
        self.RUBBER_CDB_SCHEMA_BLUE_C = QgsRubberBand(self.CANVAS_C, QgsWkbTypes.PolygonGeometry)
        self.RUBBER_LAYERS_RED_C = QgsRubberBand(self.CANVAS_C, QgsWkbTypes.PolygonGeometry)

 
        # Variable to store all available FeatureTypes.
        # The availability is defined by the existence of at least one feature of that type inside the current selected extents (bbox).
        self.FeatureTypeLayerGroups: dict = {}

        # Enhance various Qt Objects with their initial text. 
        # This is used in order to revert to the original state in reset operations when original text has already changed.

        # TAB Connection
        self.btnConnectToDbC.init_text = c.btnConnectToDbC_t
        self.btnRefreshCDBExtents.init_text = c.btnRefreshCDBExtents_t
        self.btnCityExtentsC.init_text = c.btnCityExtentsC_t
        self.btnCleanUpSchema.init_text = c.btnCleanUpSchema
        self.btnDropLayers.init_text = c.btnDropLayers

        #self.btnCreateLayers.init_text = c.btnCreateLayers_t
        #self.btnRefreshLayers.init_text = c.btnRefreshLayers_t
        #self.btnDropLayers.init_text = c.btnDropLayers_t

        ################################################
        ### SIGNALS (start) ############################
        ################################################

        #### 'User Connection' tab

        # 'Connection' group box signals
        self.cbxExistingConnC.currentIndexChanged.connect(lambda: self.evt_cbxExistingConn_changed(cdbLoader))
        
        #self.btnNewConnC.clicked.connect(self.evt_btnNewConn_clicked)
        self.btnNewConnC.clicked.connect(lambda: self.evt_btnNewConn_clicked(cdbLoader))

        # 'Database' group box signals
        self.btnConnectToDbC.clicked.connect(lambda: self.evt_btnConnectToDb_clicked(cdbLoader))
        self.cbxSchema.currentIndexChanged.connect(lambda: self.evt_cbxSchema_changed(cdbLoader))

        # Basemap (OSM) group box signals
        # Link the addition canvas to the extents qgroupbox and enable "MapCanvasExtent" options (Byproduct).
        self.qgbxExtentsC.setMapCanvas(canvas=self.CANVAS_C, drawOnCanvasOption=False)

        # Draw on Canvas tool is disabled.
        # Check Note on main>widget_setup>ws_layers_tab.py>qgbxExtents_setup
        self.qgbxExtentsC.setOutputCrs(outputCrs=self.CRS)

        # 'Extents' groupbox signals
        self.btnRefreshCDBExtents.clicked.connect(lambda: self.evt_btnRefreshCDBExtents_clicked(cdbLoader))

        self.btnCityExtentsC.clicked.connect(lambda: self.evt_btnCityExtentsC_clicked(cdbLoader))
        self.CANVAS_C.extentsChanged.connect(lambda: self.evt_canvas_ext_changed(cdbLoader))
        self.qgbxExtentsC.extentChanged.connect(lambda: self.evt_qgbxExtentsC_ext_changed(cdbLoader))

        #self.btnCreateLayers.clicked.connect(lambda: self.evt_btnCreateLayers_clicked(cdbLoader))
        #self.btnRefreshLayers.clicked.connect(lambda: self.evt_btnRefreshLayers_clicked(cdbLoader))
        #self.btnDropLayers.clicked.connect(lambda: self.evt_btnDropLayers_clicked(cdbLoader))

        self.btnCloseConnC.clicked.connect(lambda: self.evt_btnCloseConnC_clicked(cdbLoader))


        self.feat_click_count = 0
        self.groupBox.clicked.connect(lambda: self.evt_groupBox_clicked(cdbLoader))
        self.btnCleanUpSchema.clicked.connect(lambda: self.evt_btnCleanUpSchema_clicked(cdbLoader))
        self.gbxFeatSel.clicked.connect(lambda: self.evt_gbxFeatSel_clicked(cdbLoader))
        self.btnDropLayers.clicked.connect(lambda: self.evt_btnDropLayers(cdbLoader))
        ################################################
        ### SIGNALS (end) ##############################
        ################################################

    ################################################
    ### EVENTS (start) ############################
    ################################################

    ## Events for 'User connection' tab BEGIN

    #'Connection' group box events (in 'User Connection' tab)
    def evt_cbxExistingConn_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Existing Connection' comboBox (cbxExistingConnC) current index changes.
        This function runs every time the current selection of 'Existing Connection' changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.deleter_dlg

        # Set the current database connection object variable
        cdbLoader.DB: Connection = self.cbxExistingConnC.currentData()
        if not cdbLoader.DB:
            return None

        # Reset the tabs
        ct_wf.tabConnection_reset(cdbLoader)

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
        dlg = cdbLoader.deleter_dlg

        # Create/Show/Execute additional dialog for the new connection
        dlgConnector = DBConnectorDialog()
        dlgConnector.setWindowModality(2)
        dlgConnector.show()
        dlgConnector.exec_()

        # Add new connection to the Existing connections
        if dlgConnector.conn_params:
            dlg.cbxExistingConnC.addItem(f"{dlgConnector.conn_params.connection_name}", dlgConnector.conn_params)


    # 'Database' group box events (in 'User Connection' tab)
    def evt_btnConnectToDb_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the current 'Connect to {db}' pushButton
        (btnConnectToDbC) is pressed. It sets up the GUI after a click signal is emitted.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.deleter_dlg

        error_msg: str = None

        #In 'Connection Status' groupbox
        dlg.gbxConnStatusC.setDisabled(False) # Activate the connection status box (red/green checks)
        dlg.btnCloseConnC.setDisabled(False) # Activate the close connection button at the bottom

        # -------------------------------------------------------------------------------------------
        # Series of tests to be carried out when I connect as user.
        #
        # 1) Can I connect to the database? If yes, continue
        # 2) Can I connect to the qgis_pkg (and access its functions?) If yes, continue.
        # 3) Is the installed QGIS package version compatible with this version of the plugin? If yes, continue
        # 4) Is my qgis_user schema installed? If yes, continue.
        # 5) Are there cdb_schemas I am allowed to connect to? If yes, continue
        # 6) Can I connect to at least one non-empty cdb_schema? If yes, continue
        # -------------------------------------------------------------------------------------------

        # 1) Can I connect to the database? If yes, continue

        # Attempt to connect to the database, returns True/False, and if successful, store connection in cdbLoader.conn
        # Additionally, set cdbLoader.DB.pg_server_version
        successful_connection: bool = conn_f.open_and_set_connection(cdbLoader)

        if successful_connection:
            # Show database name
            dlg.lblConnToDbC_out.setText(c.success_html.format(text=cdbLoader.DB.database_name))
            dlg.requirements.is_conn_successful = True

            if cdbLoader.DB.pg_server_version is not None:
                # Show server version
                dlg.lblPostInstC_out.setText(c.success_html.format(text=cdbLoader.DB.pg_server_version))
                dlg.requirements.is_postgis_installed = True
            else:
                dlg.lblPostInstC_out.setText(c.failure_html.format(text=c.PG_SERVER_FAIL_MSG))
                dlg.requirements.is_postgis_installed = False
                #cdbLoader.DB.green_post_inst = False

                return None # Exit

        else: # Connection failed!
            ct_wf.gbxConnStatus_reset(cdbLoader)
            dlg.gbxConnStatusC.setDisabled(False)
            dlg.lblConnToDbC_out.setText(c.failure_html.format(text=c.CONN_FAIL_MSG))
            dlg.requirements.is_conn_successful = False
            #cdbLoader.DB.green_connection = False
            dlg.lblPostInstC_out.setText(c.failure_html.format(text=c.PG_SERVER_FAIL_MSG))
            dlg.requirements.is_postgis_installed = False
            #cdbLoader.DB.green_pg_server_version = False

            return None # Exit

        # 2) Can I connect to the qgis_pkg (and access its functions?) If yes, continue.

        # Check if the qgis_pkg schema (main installation) is installed in database.
        is_qgis_pkg_installed: bool = sh_sql.is_qgis_pkg_installed(cdbLoader)

        if is_qgis_pkg_installed:
            # I can now access the functions of the qgis_pkg (at least the public ones)
            # Set the current user schema name.
            sh_sql.exec_create_qgis_usr_schema_name(cdbLoader)
        else:
            dlg.lblMainInstC_out.setText(c.failure_html.format(text=c.INST_FAIL_MISSING_MSG))
            dlg.requirements.is_qgis_pkg_installed = False

            error_msg = f"The QGIS Package is not installed in this database (i.e. there is no'{cdbLoader.QGIS_PKG_SCHEMA}' schema). Please contact your database administrator."
            QMessageBox.warning(dlg, "Missing QGIS Package", error_msg)
            return None # Exit

        # 3) Is the installed QGIS package version compatible with this version of the plugin? If yes, continue

        # Get the current qgis_pkg version and check that it is compatible.
        qgis_pkg_curr_version: tuple = sh_sql.exec_qgis_pkg_version(cdbLoader)
        
        qgis_pkg_curr_version_txt      : str = qgis_pkg_curr_version[0]
        qgis_pkg_curr_version_major    : int = qgis_pkg_curr_version[2]
        qgis_pkg_curr_version_minor    : int = qgis_pkg_curr_version[3]
        qgis_pkg_curr_version_minor_rev: int = qgis_pkg_curr_version[4]

        # Only for testing purposes
        #qgis_pkg_curr_version_txt      : str = "0.7.3"
        #qgis_pkg_curr_version_major    : int = 0
        #qgis_pkg_curr_version_minor    : int = 7
        #qgis_pkg_curr_version_minor_rev: int = 3

        # Check that the QGIS Package version is >= than the minimum required for this versin of the plugin (see cdb4_constants.py)
        if (qgis_pkg_curr_version_major == c.QGIS_PKG_MIN_VERSION_MAJOR) and \
            (qgis_pkg_curr_version_minor == c.QGIS_PKG_MIN_VERSION_MINOR) and \
            (qgis_pkg_curr_version_minor_rev >= c.QGIS_PKG_MIN_VERSION_MINOR_REV):

            # Show message in Connection Status the Qgis Package is installed (and version)
            dlg.lblMainInstC_out.setText(c.success_html.format(text=" ".join([c.INST_MSG, f"(v.{qgis_pkg_curr_version_txt})"]).format(pkg=cdbLoader.QGIS_PKG_SCHEMA)))
            dlg.requirements.is_qgis_pkg_installed = True
        else:
            dlg.lblMainInstC_out.setText(c.failure_html.format(text=c.INST_FAIL_VERSION_MSG))
            dlg.requirements.is_qgis_pkg_installed = False

            error_msg: str = f"The current version of the QGIS Package installed in this database is {qgis_pkg_curr_version_txt} and is not supported anymore.\nPlease contact your database administrator and update the QGIS Package to version {c.QGIS_PKG_MIN_VERSION_TXT} (or higher)."
            QMessageBox.warning(dlg, "Unsupported version of QGIS Package", error_msg)

            return None # Exit

        # 4) Is my qgis_user schema installed? If yes, continue.

        # Check if qgis_{usr} schema (e.g. qgis_giorgio) is installed in the database.
        is_usr_schema_inst: bool = sh_sql.is_usr_schema_installed(cdbLoader)
        if is_usr_schema_inst:
            # Show message in Connection Status the 3DCityDB version if installed
            cdbLoader.DB.citydb_version: str = sh_sql.fetch_3dcitydb_version(cdbLoader)
            dlg.lbl3DCityDBInstC_out.setText(c.success_html.format(text=cdbLoader.DB.citydb_version))
            dlg.requirements.is_3dcitydb_installed = True

            # Show message in Connection Status that the qgis_{usr} schema is installed               
            dlg.lblUserInstC_out.setText(c.success_html.format(text=c.INST_MSG.format(pkg=cdbLoader.USR_SCHEMA)))
            dlg.requirements.is_usr_pkg_installed = True
        else:
            dlg.lblUserInstC_out.setText(c.failure_html.format(text=c.INST_FAIL_MSG.format(pkg=f"qgis_{cdbLoader.DB.username}")))
            dlg.requirements.is_usr_pkg_installed = False

            error_msg = f"The required user schema 'qgis_{cdbLoader.DB.username}' is missing. Please contact your database administrator to install it."
            QMessageBox.warning(dlg, "User schema not found", error_msg)

            return None # Exit

        # 5) Are there cdb_schemas I am allowed to connect to? If yes, continue

        # Get the list of 3DCityDB schemas from database as a tuple. If empty, len(tuple)=0
        cdb_schema_names_tot, cdb_schema_nums_tot = sh_sql.exec_list_cdb_schemas_all(cdbLoader)
        # Create tuples containing only non-empty cdb_schemas
        cdb_schema_names = list()
        cdb_schema_nums = list()
        for i in range(len(cdb_schema_names_tot)):
            if cdb_schema_nums_tot[i] != 0:
                cdb_schema_names.append(cdb_schema_names_tot[i])
                cdb_schema_nums.append(cdb_schema_nums_tot[i])
        cdb_schema_names = tuple(cdb_schema_names)
        cdb_schema_nums = tuple(cdb_schema_nums)

        if len(cdb_schema_names_tot) == 0: 
            # Inform the user that there are no cdb_schemas to be chosen from.
            error_msg: str = f"No citydb schemas could be retrieved from the database. You may lack proper privileges to access them.\nPlease contact your database administrator."
            QMessageBox.warning(dlg, "No accessible citydb schemas found", error_msg)
            
            return None # Exit

        else:
            if len(cdb_schema_names) == 0:
                # Inform the use that all available cdb schemas are empty.
                error_msg = "The available citydb schema(s) is/are all empty. Please load data into the database first."
                QMessageBox.warning(dlg, "Empty citydb schema(s)", "The available citydb schema(s) is/are all empty. Please load data into the database first.")
                
                return None

            else: # Finally, we have all conditions to fill the cdb_schema combobox
                uc_tf.fill_cdb_schemas_box(cdbLoader, cdb_schemas=cdb_schema_names)
                # At this point, filling the schema box, activates the 'evt_cbxSchema_changed' event.
                # So if you're following the code line by line, go to citydb_loader.py>evt_cbxSchema_changed or at 'cbxSchema_setup' function below

        return None # Exit


    def evt_cbxSchema_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'schemas' comboBox (cbxSchema) current index changes.
        Function to setup the GUI after an 'indexChanged' signal is emitted from the cbxSchema combo box.
        This function runs every time the selected schema is changed (in 'User Connection' tab)
        Checks if the connection + schema meet the necessary requirements.
        """
        dlg = cdbLoader.deleter_dlg

        # Set the current schema variable
        cdbLoader.CDB_SCHEMA: str = dlg.cbxSchema.currentText()
        # By now, the schema variable must have be assigned.
        if not dlg.cbxSchema.currentData():
            return None

        # Enable schema comboBox
        dlg.cbxSchema.setDisabled(False)
        dlg.lblSchema.setDisabled(False)

        ''' CDBDeleter '''
        # enable 'Clean up schema' and 'Truncate ALL'
        dlg.groupBox.setDisabled(False)
        dlg.groupBox_2.setDisabled(False)
        dlg.gbxFeatSel.setDisabled(False)
        # change 'Truncate ALL' current text
        dlg.btnCleanUpSchema.setText(dlg.btnCleanUpSchema.init_text.format(sch=cdbLoader.CDB_SCHEMA))
        dlg.btnDropLayers.setText(c.btnDropLayers.format(sch=cdbLoader.CDB_SCHEMA))
        ''' CDBDeleter '''

        dlg.btnRefreshCDBExtents.setText(dlg.btnRefreshCDBExtents.init_text.format(sch=cdbLoader.CDB_SCHEMA))
        dlg.btnCityExtentsC.setText(dlg.btnCityExtentsC.init_text.format(sch=cdbLoader.CDB_SCHEMA))

        dlg.gbxBasemapC.setDisabled(False)

        # Setup the 'Basemap (OSM)' groupbox.
        ct_wf.gbxBasemapC_setup(cdbLoader)

        layer_extents_wkt: str = sql.fetch_precomputed_extents(cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, ext_type=c.MAT_VIEW_EXT_TYPE)
        if layer_extents_wkt:
            # Put extents coordinates into the widget. Signal emitted for qgbxExtentsC.
            dlg.qgbxExtentsC.setOutputExtentFromUser(QgsRectangle.fromWkt(layer_extents_wkt), self.CRS)


        # Check that DB is configured correctly. If so, enable all following buttons etc.
        #if cdbLoader.DB.user_meets_requirements():
        if dlg.requirements.are_requirements_fulfilled():
            dlg.tabLayers.setDisabled(False)
            dlg.lblInfoText.setDisabled(False)
            dlg.lblInfoText.setText(dlg.lblInfoText.init_text.format(db=cdbLoader.DB.database_name, usr=cdbLoader.DB.username, sch=cdbLoader.CDB_SCHEMA))
            dlg.gbxBasemap.setDisabled(False)
            dlg.qgbxExtents.setDisabled(False)
            dlg.btnCityExtents.setDisabled(False)
            dlg.btnCityExtents.setText(dlg.btnCityExtents.init_text.format(sch="layers extents"))
        
        return None

    def evt_groupBox_clicked(self, cdbLoader: CDBLoader):

        dlg = cdbLoader.deleter_dlg
        # if checked:
            # enable 'Truncate ALL'
            # disable feature selection
        if dlg.groupBox.isChecked():
            dlg.btnDropLayers.setDisabled(True)
            dlg.btnCleanUpSchema.setDisabled(False)
            dlg.gbxFeatSel.setDisabled(True)
        # if unchecked:
            # do the opposite
        if not(dlg.groupBox.isChecked()):
            dlg.btnCleanUpSchema.setDisabled(True)
            dlg.gbxFeatSel.setDisabled(False)
            dlg.btnDropLayers.setDisabled(False)

    def evt_btnCleanUpSchema_clicked(self,cdbLoader: CDBLoader):

        dlg = cdbLoader.deleter_dlg
        res = QMessageBox.question(dlg, "Cleanup Schema", f"You are about to delete all CityGML features in the schema '{cdbLoader.CDB_SCHEMA}'. Proceed ?")
        if res == 16384:
            with cdbLoader.conn.cursor() as cur:
                cur.execute(f"""SELECT {cdbLoader.CDB_SCHEMA}.cleanup_schema()""")
                cdbLoader.conn.commit()
        else:
            return

    def evt_gbxFeatSel_clicked(self,cdbLoader: CDBLoader):

        dlg = cdbLoader.deleter_dlg

        if dlg.gbxFeatSel.isChecked():
            dlg.groupBox.setDisabled(True)
            dlg.btnDropLayers.setDisabled(False)
        if not(dlg.gbxFeatSel.isChecked()):
            dlg.groupBox.setDisabled(False)
            dlg.btnDropLayers.setDisabled(True)

        extent = None
        if self.delete_extent:
            extent = self.delete_extent
        else:
            extent = cdbLoader.CDB_SCHEMA_EXTENTS_BLUE

        if bool(not(self.feat_click_count)):

                root_classes = sql.get_root_classes(cdbLoader,extent)
                for root in root_classes:
                    dlg.mComboBox_2.addItemWithCheckState(root, 0)
                types = sql.get_feature_types(cdbLoader,extent)
                for ftype in types:
                    dlg.cbxFeatType.addItemWithCheckState(ftype,0)

                self.feat_click_count += 1





    # 'Basemap (OSM)' group box events (in 'User Connection' tab)
    def evt_canvas_ext_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the current canvas extents (pan over map) changes.
        Reads the new current extents from the map and sets it in the 'Extents'
        (qgbxExtentsC) widget.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.deleter_dlg

        # Get canvas's current extent
        extent: QgsRectangle = self.CANVAS_C.extent()
        self.delete_extent = extent
        # Set the current extent to show in the 'extent' widget.
        dlg.qgbxExtentsC.setCurrentExtent(currentExtent=extent, currentCrs=self.CRS)
        dlg.qgbxExtentsC.setOutputCrs(outputCrs=self.CRS)

        if bool(self.delete_extent.xMaximum()) and dlg.gbxFeatSel.isChecked():
            dlg.mComboBox_2.clear()
            dlg.cbxFeatType.clear()
            root_classes = sql.get_root_classes(cdbLoader, extent)
            for root in root_classes:
                dlg.mComboBox_2.addItemWithCheckState(root, 0)
            types = sql.get_feature_types(cdbLoader, extent)
            for ftype in types:
                dlg.cbxFeatType.addItemWithCheckState(ftype, 0)

    def evt_btnDropLayers(self,cdbLoader: CDBLoader):

        dlg = cdbLoader.deleter_dlg
        from threading import Thread

        if len(dlg.cbxFeatType.checkedItems()):
            with cdbLoader.conn.cursor() as cur:
                for item in dlg.cbxFeatType.checkedItems():
                    gmlid_query = f'''SELECT co.id FROM {cdbLoader.CDB_SCHEMA}.cityobject as co
                                      WHERE (co.envelope && ST_MakeEnvelope({self.delete_extent.xMinimum()},
                                      {self.delete_extent.yMinimum()}, {self.delete_extent.xMaximum()},
                                      {self.delete_extent.yMaximum()},28992)) AND 
                                      co.objectclass_id = (SELECT id FROM {cdbLoader.CDB_SCHEMA}.objectclass
                                                           WHERE classname = '{item}')
                                      '''

                    cur.execute(gmlid_query)
                    ids = [idx[0] for idx in cur.fetchall()]

                    #for objid in ids:
                    delete_query = f'''SELECT {cdbLoader.CDB_SCHEMA}.del_cityobject(ARRAY {ids})'''
                    t = Thread(target=cur.execute, args=[delete_query])
                    t.start()
                    cdbLoader.conn.commit()

        # repeat for root classes


    def evt_qgbxExtentsC_ext_changed(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Extents' groubBox (qgbxExtentsC) extent in widget changes.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.deleter_dlg

        # Update current extents variable with the ones that fired the signal.
        self.CURRENT_EXTENTS: QgsRectangle = dlg.qgbxExtentsC.outputExtent()
        if self.CURRENT_EXTENTS.isNull() or self.CDB_SCHEMA_EXTENTS_BLUE.isNull():
            return None

        # Draw the red rubber band corresponding to the next extents of the basemap (basemap)
        canvas.insert_rubber_band(band=self.RUBBER_LAYERS_RED_C, extents=self.CURRENT_EXTENTS, crs=self.CRS, width=2, color=Qt.red)

        # Compare original extents with user defined ones.
        layer_extents = QgsGeometry.fromRect(self.CURRENT_EXTENTS)
        cdb_extents = QgsGeometry.fromRect(self.CDB_SCHEMA_EXTENTS_BLUE)

        # Check validity of user extents relative to the City Model's cdb_extents.
        if layer_extents.intersects(cdb_extents):
            self.LAYER_EXTENTS_RED = self.CURRENT_EXTENTS           
        else:
            QMessageBox.critical(dlg, "Warning", f"Pick a region intersecting the extents of '{cdbLoader.CDB_SCHEMA}' (blue area).")
            return None


    def evt_btnRefreshCDBExtents_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the button (btnRefreshCDBExtents) is pressed.
        It will check whether the cdb_extents
        - are null, i.e. the database has been emptied (reset all, the cdb_schema will disappear from the list)
        - have not changed (do nothing)
        - have changed and the new cdb extents contain the old ones (only update the ribbons)
        - have changed and the new cdb extents do not strictly contain the old ones (drop existing layers, update ribbons)
        """
        is_geom_null, x_min, y_min, x_max, y_max, srid = sql.exec_compute_cdb_schema_extents(cdbLoader=cdbLoader)
        srid = None # Discard unneeded variable.

        if not is_geom_null:

            cdb_extents_old: QgsRectangle = self.CDB_SCHEMA_EXTENTS_BLUE
            
            cdb_extents_new = QgsRectangle()
            cdb_extents_new.set(x_min, y_min, x_max, y_max, False)

            #########################################
            # Only for testing purposes
            #cdb_extents_new.set(-200, 0, -150, 50, False)
            #cdb_extents_new = cdb_extents_new.buffered(50.0)
            #########################################

            if cdb_extents_new == cdb_extents_old:
                # Do nothing, the extents have not changed. No need to do anything
                QgsMessageLog.logMessage(f"Extents of '{cdbLoader.CDB_SCHEMA}' are unchanged. No need to update them.", cdbLoader.PLUGIN_NAME, level=Qgis.Info, notifyUser=True)
                return None
            else:
                # The extents have changed. Show them on the map as dashed line

                # Backup the original Layer extents (red)
                # (They will be changed by the event evt_qgbxExtentsC_ext_changed later on)
                layer_extents_wkt: str = self.LAYER_EXTENTS_RED.asWktPolygon()
                temp_layer_extents: QgsRectangle = QgsRectangle().fromWkt(layer_extents_wkt)

                # Create the extents containing both old and new cdb_schema extents
                cdb_extents_union: QgsRectangle = QgsRectangle(cdb_extents_old)
                cdb_extents_union.combineExtentWith(cdb_extents_new)

                # Create new rubber band
                cdb_extents_new_rubber_band: QgsRubberBand = QgsRubberBand(self.CANVAS_C, QgsWkbTypes.PolygonGeometry)
                cdb_extents_new_rubber_band.setLineStyle(Qt.DashLine)

                # Set up the canvas to the new extents of the cdb_schema.
                # Fires evt_qgbxExtentsC_ext_changed and evt_canvas_ext_changed
                canvas.canvas_setup(cdbLoader=cdbLoader, canvas=self.CANVAS_C, extents=cdb_extents_union, crs=self.CRS, clear=False)

                # Reset the red layer extents to the original size
                self.LAYER_EXTENTS_RED = temp_layer_extents

                # Add the rubber bands 
                canvas.insert_rubber_band(band=cdb_extents_new_rubber_band, extents=cdb_extents_new, crs=self.CRS, width=3, color=Qt.blue)
                canvas.insert_rubber_band(band=self.RUBBER_CDB_SCHEMA_BLUE_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE, crs=self.CRS, width=3, color=Qt.blue)
                canvas.insert_rubber_band(band=self.RUBBER_LAYERS_RED_C, extents=temp_layer_extents, crs=self.CRS, width=2, color=Qt.red)

                # Zoom to the rubber band of the new cdb_extents.
                # Fires evt_canvas_ext_changed
                canvas.zoom_to_extents(canvas=self.CANVAS_C, extents=cdb_extents_union)

                if cdb_extents_new.contains(self.LAYER_EXTENTS_RED):

                    msg: str = f"Extents of '{cdbLoader.CDB_SCHEMA}' have changed (blue dashed line). Now they will be automatically updated."
                    QMessageBox.warning(cdbLoader.deleter_dlg, "Extents changed!", msg)

                    # Update the cdb_extents, leave the layer_extents and the layers
                    # Update the canvas and the rubber bands in both tabs.

                    # Update the cdb_extents in the database
                    sql.exec_upsert_extents(cdbLoader=cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, bbox_type=c.CDB_SCHEMA_EXT_TYPE, extents_wkt_2d_poly=cdb_extents_new.asWktPolygon())

                    # Update canvas and rubber bands in TAB Connection

                    # Drop the existing rubber bands, they need to be redone
                    cdb_extents_new_rubber_band.reset()
                    self.RUBBER_CDB_SCHEMA_BLUE_C.reset()
                    self.RUBBER_LAYERS_RED_C.reset()

                    self.CDB_SCHEMA_EXTENTS_BLUE = cdb_extents_new

                    # Set up the canvas to the new extents of the cdb_schema.
                    # Fires evt_qgbxExtentsC_ext_changed and evt_canvas_ext_changed
                    canvas.canvas_setup(cdbLoader=cdbLoader, canvas=self.CANVAS_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE, crs=self.CRS, clear=False)
                    # Reset the layer extents after the previous function modifies them
                    self.LAYER_EXTENTS_RED = temp_layer_extents

                    canvas.insert_rubber_band(band=self.RUBBER_CDB_SCHEMA_BLUE_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE, crs=self.CRS, width=3, color=Qt.blue)
                    canvas.insert_rubber_band(band=self.RUBBER_LAYERS_RED_C, extents=temp_layer_extents, crs=self.CRS, width=2, color=Qt.red)

                    canvas.zoom_to_extents(canvas=self.CANVAS_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE)

                    # Reset the layer extents after the previous function modifies them
                    self.LAYER_EXTENTS_RED = temp_layer_extents

                    return None
                else: # The new cdb_extents do not contain the old ones.

                    # Question? Do you want to update the bbox and proceed?
                    msg: str = f"Extents of '{cdbLoader.CDB_SCHEMA}' have changed (dashed blue line). This requires to drop the existing layers\n\nDo you want to proceed?"
                    res = QMessageBox.question(cdbLoader.deleter_dlg, "Extents changed!", msg)
                    if res == 16384: # YES, proceed with updating the bbox

                        # Update the cdb_extents in the database
                        sql.exec_upsert_extents(cdbLoader=cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, bbox_type=c.CDB_SCHEMA_EXT_TYPE, extents_wkt_2d_poly=cdb_extents_new.asWktPolygon())

                        # Update canvas and rubber bands in TAB Connection
                        cdb_extents_new_rubber_band.reset()
                        self.RUBBER_CDB_SCHEMA_BLUE_C.reset()
                        self.RUBBER_LAYERS_RED_C.reset()

                        self.CDB_SCHEMA_EXTENTS_BLUE = cdb_extents_new
                        self.LAYER_EXTENTS_RED = cdb_extents_new

                        # Set up the canvas to the new extents of the cdb_schema.
                        # Fires evt_qgbxExtentsC_ext_changed and evt_canvas_ext_changed
                        canvas.canvas_setup(cdbLoader=cdbLoader, canvas=self.CANVAS_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE, crs=self.CRS, clear=False)
                        # Reset the layer extents after the previous function modifies them
                        self.LAYER_EXTENTS_RED = cdb_extents_new

                        canvas.insert_rubber_band(band=self.RUBBER_CDB_SCHEMA_BLUE_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE, crs=self.CRS, width=3, color=Qt.blue)
                        canvas.insert_rubber_band(band=self.RUBBER_LAYERS_RED_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE, crs=self.CRS, width=2, color=Qt.red)

                        canvas.zoom_to_extents(canvas=self.CANVAS_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE)

                        return None 

                    else: 
                        # Do nothing, revert to previous situation.
                        cdb_extents_new_rubber_band.reset()
                        canvas.zoom_to_extents(self.CANVAS_C, cdb_extents_old)
                        return None
        else:
            # This is the case when the database has been emptied.

            # Inform the user
            msg: str = f"The '{cdbLoader.CDB_SCHEMA}' schema has been emptied. It will disappear from the drop down menu untill you upload new data again."
            QMessageBox.information(cdbLoader.deleter_dlg, "Extents changed!", msg)
            QgsMessageLog.logMessage(msg, cdbLoader.PLUGIN_NAME, level=Qgis.Info, notifyUser=True)

            # Reset to null the cdb_extents in the extents table in PostgreSQL
            sql.exec_upsert_extents(cdbLoader=cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, bbox_type=c.CDB_SCHEMA_EXT_TYPE, extents_wkt_2d_poly=None)
            # Reset to null the layers_extents in the extents table in PostgreSQL
            sql.exec_upsert_extents(cdbLoader=cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, bbox_type=c.MAT_VIEW_EXT_TYPE, extents_wkt_2d_poly=None)

            # Drop the layers (if necessary)
            #if cdbLoader.deleter_dlg.btnDropLayers.isEnabled():
            #    thr.drop_layers_thread(cdbLoader) # This already disables the layers tab

            # Close the connection
            if cdbLoader.conn is not None:
                cdbLoader.conn.close()

            # Reconnect and reset the list of the cdb_schemas in the combobox
            self.evt_btnConnectToDb_clicked(cdbLoader)
            return None

        
    def evt_btnCityExtentsC_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the current 'Calculate from City model' pushButton (btnCityExtentsC) is pressed.
        """
        # Variable to store the plugin main dialog.
        dlg = cdbLoader.deleter_dlg

        # Get the extents stored in server (already computed at this point).
        cdb_extents_wkt: str = sql.fetch_precomputed_extents(cdbLoader, usr_schema=cdbLoader.USR_SCHEMA, cdb_schema=cdbLoader.CDB_SCHEMA, ext_type=c.CDB_SCHEMA_EXT_TYPE)
        #assert cdb_extents_wkt, "Extents don't exist, but they should have been actually already computed!"

        # Convert extents format to QgsRectangle object.
        cdb_extents = QgsRectangle.fromWkt(cdb_extents_wkt)
        # Update extents in plugin variable.
        self.CDB_SCHEMA_EXTENTS_BLUE = cdb_extents
        self.CURRENT_EXTsENTS = cdb_extents

        # Put extents coordinates into the widget.
        dlg.qgbxExtentsC.setOutputExtentFromUser(self.CURRENT_EXTENTS, self.CRS)
        # At this point an extentChanged signal is emitted.

        # Zoom to layer extents (red box).
        canvas.zoom_to_extents(canvas=self.CANVAS_C, extents=self.CDB_SCHEMA_EXTENTS_BLUE)


    def evt_btnCloseConnC_clicked(self, cdbLoader: CDBLoader) -> None:
        """Event that is called when the 'Close current connection' pushButton (btnCloseConn) is pressed.
        """
        ct_wf.tabConnection_reset(cdbLoader)

    ### EVENTS (end) ############################