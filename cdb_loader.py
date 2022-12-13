# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CDB4Loader
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
import os.path
import typing

from qgis.PyQt.QtCore import Qt, QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QWidget, QProgressBar, QVBoxLayout
from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgisInterface, QgsMessageBar
import psycopg2

from . import main_constants as main_c
from .resources import qInitResources

from .cdb4.gui_db_connector.other_classes import Connection

class CDBLoader:
    """QGIS Plugin Implementation. Main class.
    """

    def __init__(self, iface: QgisInterface) -> None:
        """CDBLoader class Constructor.

        *   :param iface: An interface instance that will be passed to this
                class which provides the hook by which you can manipulate the
                QGIS application at run time.

            :type iface: QgsInterface
        """
        # Variable referencing to the QGIS interface.
        self.iface: QgisInterface = iface

        # Initialize Qt resources from file resources.py.
        qInitResources()

        # initialize plugin full path (including plugin directory).
        self.PLUGIN_ABS_PATH: str = os.path.normpath(os.path.dirname(__file__))

        #Initialize constants
        # QGIS current version
        self.QGIS_VERSION_STR: str = Qgis.version() 
        self.QGIS_VERSION_MAJOR: int = int(self.QGIS_VERSION_STR.split(".")[0])
        self.QGIS_VERSION_MINOR: int = int(self.QGIS_VERSION_STR.split(".")[1])
        self.QGIS_VERSION_REV: int   = int(self.QGIS_VERSION_STR.split(".")[2].split("-")[0])

        # Read and assign constants from main_constants file (main_c)
        self.PLUGIN_NAME: str = main_c.PLUGIN_NAME
        self.PLUGIN_NAME_ADMIN: str = main_c.PLUGIN_NAME_ADMIN
        self.PLUGIN_VERSION_MAJOR: int = main_c.PLUGIN_VERSION_MAJOR
        self.PLUGIN_VERSION_MINOR: int = main_c.PLUGIN_VERSION_MINOR
        self.PLUGIN_VERSION_REV: int = main_c.PLUGIN_VERSION_REV
        self.PLUGIN_VERSION_TXT: str = ".".join([str(self.PLUGIN_VERSION_MAJOR), str(self.PLUGIN_VERSION_MINOR), str(self.PLUGIN_VERSION_REV)])

        QgsMessageLog.logMessage(f"You are using 3DCityDB-Loader v. {self.PLUGIN_VERSION_TXT}. Enjoy!", self.PLUGIN_NAME, level=Qgis.Info, notifyUser=False)

        self.QGIS_PKG_SCHEMA: str = main_c.QGIS_PKG_SCHEMA
        self.CDB4_PLUGIN_DIR: str = main_c.CDB4_PLUGIN_DIR

        # Dialog names
        self.ADMIN_DLG: str = main_c.ADMIN_DLG
        self.LOADER_DLG: str = main_c.LOADER_DLG
        self.DELETER_DLG: str = main_c.DELETER_DLG

        # Variable to store the selected citydb schema name.
        self.CDB_SCHEMA: str = None
        # Variable to store the selected {usr_schema} name.
        self.USR_SCHEMA: str = main_c.USR_SCHEMA

        # Variable to store the user dialog of the plugin.
        self.loader_dlg = None
        # Variable to store the admin dialog of the plugin.
        self.admin_dlg = None

        # Variable to store the current open connection of a database.
        self.conn: psycopg2.connection = None

        # Variable to store the existing connection object.
        self.DB: Connection = None

        # initialize locale.
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.PLUGIN_ABS_PATH, "i18n", "DBLoader_{}.qm".format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes.
        self.actions: list = []

        # Check if plugin was started the first time in current QGIS session.
        # Must be set in initGui() to survive plugin reloads.
        self.first_start_loader: bool = True
        self.first_start_admin: bool = True


    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.

        *   :param message: String for translation.
            :type message: str

        *   :returns: Translated version of message.
            :rtype: str
        """
        return QCoreApplication.translate("DBLoader", message)


    def add_action(self,
            icon_path: str,
            txt: str,
            callback: typing.Callable[..., None],
            enabled_flag: bool = True,
            add_to_menu: bool = True,
            add_to_toolbar: bool = True,
            status_tip: typing.Optional[str] = None,
            whats_this: typing.Optional[str] = None,
            parent: typing.Optional[QWidget] = None) -> QAction:
        """Add a toolbar icon to the toolbar.

        *   :param icon_path: Path to the icon for this action. Can be a
                resource path (e.g. ":/plugins/foo/bar.png") or a normal
                file system path.
            :type icon_path: str

        *   :param txt: Text that should be shown in menu items for this
                action.
            :type txt: str

        *   :param callback: Function to be called when the action is
                triggered.
            :type callback: function

        *   :param enabled_flag: A flag indicating if the action should be
                enabled by default. Defaults to True.
            :type enabled_flag: bool

        *   :param add_to_menu: Flag indicating whether the action should also
                be added to the menu. Defaults to True.
            :type add_to_menu: bool

        *   :param add_to_toolbar: Flag indicating whether the action should
                also be added to the toolbar. Defaults to True.
            :type add_to_toolbar: bool

        *   :param status_tip: Optional text to show in a popup when mouse
                pointer hovers over the action.
            :type status_tip: str

        *   :param whats_this: Optional text to show in the status bar when the
                mouse pointer hovers over the action.
            :type whats_this: str

        *   :param parent: Parent widget for the new action. Defaults None.
            :type parent: QWidget

        *   :returns: The action that was created. Note that the action is also
                added to self.actions list.
            :rtype: QAction
        """
        # Create icon from referenced path in resources file.
        icon = QIcon(icon_path)

        # Create action object
        action = QAction(icon=icon, text=txt, parent=parent)

        # Signal to run plugin when clicked (execute main method: run())
        action.triggered.connect(callback)

        # Set the name of the action
        action.setObjectName(txt)

        # Set the action as enabled (not greyed out)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(statusTip=status_tip)

        if whats_this is not None:
            action.setWhatsThis(what=whats_this)

        # Adds plugin to "Database" toolbar.
        if add_to_toolbar:
            self.iface.addDatabaseToolBarIcon(qAction=action)

        # Adds plugin to "Database" menu.
        if add_to_menu:
            # In order to add the plugin into the database menu we
            # follow the 'hacky' approach below to bypass possibly a bug:
            #
            # The bug: Using the method addPluginToDatabaseMenu causes
            # the plugin to be inserted in a submenu of itself
            # 3DCityDB-Loader > 3DCityDB-Loader which we don't want.
            # However using the addAction method to insert the plugin directly,
            # causes the database menu to 'pop out' of the menu ribbon in a
            # hidden state. Note that this method, for some bizarre reasons,
            # works for all the menus except the database menu.
            # Using the addPluginToDatabaseMenu method BEFORE the addAction
            # method seems to bypass this issue. Needs further investigation.

            # Add the action to the database menu (bug countermeasure)
            self.iface.addPluginToDatabaseMenu(name=main_c.PLUGIN_NAME, action=action)

            # Add the action to the database menu
            #self.iface.databaseMenu().addAction(action)

            # Now that we made sure that the bug didn't occur, remove it.
            # self.iface.removePluginDatabaseMenu(name=txt, action=action)

        self.actions.append(action)

        return action


    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI.
        """
        # The icon path is set from the compiled resources file (in main dir).
        loader_icon_path = ":/plugins/citydb_loader/icons/plugin_icon.png"
        adm_icon_path = ":/plugins/citydb_loader/icons/settings_icon.svg"

        # Loader plugin
        self.add_action(
            icon_path = loader_icon_path,
            txt = self.tr(self.PLUGIN_NAME),
            callback = self.run_loader,
            parent = self.iface.mainWindow(),
            add_to_toolbar = True)

        # Admin plugin
        self.add_action(
            icon_path = adm_icon_path,
            txt = self.tr(self.PLUGIN_NAME_ADMIN),
            callback = self.run_admin,
            parent = self.iface.mainWindow(),
            add_to_toolbar = True) # Default: False (but useful to set it to True in development mode).

        # Will be set False in run_user(), run_admin()
        self.first_start_loader = True
        self.first_start_admin = True


    def unload(self) -> None:
        """Removes the plugin menu item and icon from QGIS GUI.
        """
        for action in self.actions:
            self.iface.removeDatabaseToolBarIcon(qAction=action)
            self.iface.removePluginDatabaseMenu(name=self.PLUGIN_NAME, action=action)


    def run_admin(self) -> None:
        """Run main method that performs all the real work.
        -   Creates the plugin dialog
        -   Instantiates the plugin main class (CDB4LoaderAdminDialog) with its GUI
        -   Setups the plugin signals
        -   Executes the main dialog
        """
        from .cdb4.gui_admin.cdb4_admin_dialog import CDB4AdminDialog # Admin dialog
        from .cdb4.gui_admin.functions import tab_conn_widget_functions as dba_wf
        from .cdb4.gui_db_connector.functions import conn_functions as conn_f

        # Only create GUI ONCE in callback, so that it will only load when the plugin is started.
        if self.first_start_admin:
            self.first_start_admin = False
            # Create the dialog with elements (after translation).
            self.admin_dlg = CDB4AdminDialog(cdbLoader=self)

        # Get existing connections from QGIS profile settings.
        conn_f.get_qgis_postgres_conn_list(self) # Stored in self.conn

        # When this dialogue is open, inputs in any other windows are blocked.
        self.admin_dlg.setWindowModality(2)

        # Show the dialog
        self.admin_dlg.show()

        # Run the dialog event loop.
        res = self.admin_dlg.exec_()
        if not res: # Dialog has closed (X button was pressed)
            # Reset the dialog widgets. (Closes the current open connection.)
            dba_wf.tabDbAdmin_reset(self)


    def run_loader(self) -> None:
        """Run main method that performs all the real work.
        -   Creates the plugin dialog
        -   Instantiates the plugin main class (CDB4LoaderUserDialog) with its GUI
        -   Setups the plugin signals
        -   Executes the main dialog
        """
        from .cdb4.gui_loader.cdb4_loader_dialog import CDB4LoaderDialog # User dialog
        from .cdb4.gui_db_connector.functions import conn_functions as conn_f        

        # Only create GUI ONCE in callback,
        # so that it will only load when the plugin is started.
        if self.first_start_loader:
            self.first_start_loader = False

            # Create the dialog with elements (after translation).
            self.loader_dlg = CDB4LoaderDialog(cdbLoader=self)

            dlg = self.loader_dlg

            # Replace empty graphics view widget with Map canvas.
            dlg.gLayoutBasemapC.replaceWidget(dlg.gvCanvasC, dlg.CANVAS_C)
            dlg.vLayoutBasemap.replaceWidget(dlg.gvCanvas, dlg.CANVAS_L)

            # Remove empty graphics View widget from dialog.
            dlg.gvCanvasC.setParent(None)
            dlg.gvCanvas.setParent(None)

            # Get existing connections from QGIS profile settings.
            conn_f.get_qgis_postgres_conn_list(self) # Stored in self.conn

        # Show the dialog
        self.loader_dlg.show()

        # Run the dialog event loop.
        res = self.loader_dlg.exec_() 
        if not res: # Dialog has closed (X button was pressed)
            return None


    def evt_update_bar(self, dialog_name: str, step: int, text: str) -> None:
        """Function to setup the progress bar upon update. Important: Progress Bar needs to be already created
        in CDBLoader.msg_bar: QgsMessageBar and CDBLoader.bar: QProgressBar.
        This event is not linked to any widet_setup function as it isn't responsible for changes in different 
        widgets in the gui.

        *   :param dialog: The dialog to hold the bar.
            e.g. "admin_dlg" or "loader_dlg"
            :type step: str

        *   :param step: Current value of the progress
            :type step: int

        *   :param text: Text to display on the bar
            :type text: str
        """

        if dialog_name == self.ADMIN_DLG:         #"admin_dlg"
            progress_bar = self.admin_dlg.bar
        elif dialog_name == self.LOADER_DLG:      # "loader_dlg":
            progress_bar = self.loader_dlg.bar
        #elif dialog_name == self.DELETER_DLG:      # "deleter_dlg":
            #progress_bar = self.deleter_dlg.bar

        # Show text instead of completed percentage.
        if text:
            progress_bar.setFormat(text)

        # Update progress with current step
        progress_bar.setValue(step)


    def create_progress_bar(self, dialog, layout: QVBoxLayout, position: int) -> None:
        """Function that creates a QProgressBar embedded into a QgsMessageBar, in a specific position in the GUI.

        *   :param layout: QLayout of the gui where the bar is to be
                assigned.
            :type layout: QBoxLayout

        *   :param position: The place (index) in the layout to place
                the progress bar
            :type position: int
        """
        # Create QgsMessageBar instance.
        dialog.msg_bar = QgsMessageBar()

        # Add the message bar into the input layer and position.
        layout.insertWidget(position, dialog.msg_bar)

        # Create QProgressBar instance into QgsMessageBar.
        dialog.bar = QProgressBar(parent=dialog.msg_bar)

        # Setup progress bar.
        dialog.bar.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        dialog.bar.setStyleSheet("text-align: left;")

        # Show progress bar in message bar.
        dialog.msg_bar.pushWidget(dialog.bar, Qgis.Info)