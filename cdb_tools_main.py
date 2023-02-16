"""
/***************************************************************************
 Class CDBToolsMain
 
        This is a QGIS plugin for the CityGML 3D City Database.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-09-30
        git sha              : $Format:%H$
        author(s)            : Giorgio Agugiaro
                               Konstantinos Pantelios
        email                : g.agugiaro@tudelft.nl
                               konstantinospantelios@yahoo.com
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
from qgis.PyQt.QtWidgets import QAction, QWidget, QProgressBar, QVBoxLayout, QDialog
from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgisInterface, QgsMessageBar

from .resources import qInitResources
from . import cdb_tools_main_constants as main_c

class CDBToolsMain:
    """QGIS Plugin Implementation. Main class.
    """

    def __init__(self, iface: QgisInterface) -> None:
        """CDBToolsMain class Constructor.

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
        self.QGIS_VERSION_REV:   int = int(self.QGIS_VERSION_STR.split(".")[2].split("-")[0])

        # Read and assign constants from main_constants file (main_c)
        self.PLUGIN_NAME: str = main_c.PLUGIN_NAME_LABEL
        self.PLUGIN_NAME_ADMIN:   str = main_c.PLUGIN_NAME_ADMIN_LABEL
        self.PLUGIN_NAME_LOADER:  str = main_c.PLUGIN_NAME_LOADER_LABEL
        self.PLUGIN_NAME_DELETER: str = main_c.PLUGIN_NAME_DELETER_LABEL
        
        self.PLUGIN_VERSION_MAJOR: int = main_c.PLUGIN_VERSION_MAJOR
        self.PLUGIN_VERSION_MINOR: int = main_c.PLUGIN_VERSION_MINOR
        self.PLUGIN_VERSION_REV:   int = main_c.PLUGIN_VERSION_REV
        self.PLUGIN_VERSION_TXT:   str = ".".join([str(self.PLUGIN_VERSION_MAJOR), str(self.PLUGIN_VERSION_MINOR), str(self.PLUGIN_VERSION_REV)])

        # Welcome message upon (re)loading
        msg: str = f"<br><br>------ WELCOME! -------<br>You are using the <b>{self.PLUGIN_NAME} v. {self.PLUGIN_VERSION_TXT} GIO-DEV</b> plugin for <b>QGIS v. {self.QGIS_VERSION_MAJOR}.{self.QGIS_VERSION_MINOR}.{self.QGIS_VERSION_REV}</b>.<br>-----------------------------<br>"
        QgsMessageLog.logMessage(msg, self.PLUGIN_NAME, level=Qgis.Info, notifyUser=False)

        self.QGIS_PKG_SCHEMA: str = main_c.QGIS_PKG_SCHEMA
        self.CDB4_PLUGIN_DIR: str = main_c.CDB4_PLUGIN_DIR

        # Dialog names
        self.DLG_NAME_ADMIN: str = main_c.DLG_NAME_ADMIN
        self.DLG_NAME_LOADER: str = main_c.DLG_NAME_LOADER
        self.DLG_NAME_DELETER: str = main_c.DLG_NAME_DELETER

        # Variable to store the loader dialog of the plugin.
        self.loader_dlg = None
        # Variable to store the deleter dialog of the plugin.
        self.deleter_dlg = None
        # Variable to store the admin dialog of the plugin.
        self.admin_dlg = None

        # Check if plugin was started the first time in current QGIS session. Must be set in initGui() to survive plugin reloads.
        self.first_start_loader: bool = True
        self.first_start_deleter: bool = True
        self.first_start_admin: bool = True

        # initialize locale.
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.PLUGIN_ABS_PATH, "i18n", "DBLoader_{}.qm".format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes.
        self.actions: list = []


    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API. We implement this ourselves since we do not inherit QObject. 

        *   :param message: String for translation.
            :type message: str

        *   :returns: Translated version of message.
            :rtype: str
        """
        return QCoreApplication.translate("3DCityDB Manager", message)


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
            # In order to add the plugin into the database menu we follow the 'hacky' approach below to bypass possibly a bug:
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
            self.iface.addPluginToDatabaseMenu(name=self.PLUGIN_NAME, action=action)

            # Add the action to the database menu
            #self.iface.databaseMenu().addAction(action)

            # Now that we made sure that the bug didn't occur, remove it.
            # self.iface.removePluginDatabaseMenu(name=txt, action=action)

        self.actions.append(action)

        return action


    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI.
        """
        # The icon path is set from the compiled resources file (in main dir), or directly with path to the file.
        # admin_icon_path   = ":/plugins/citydb_loader/icons/settings_icon.svg"
        loader_icon_path  = os.path.join(self.PLUGIN_ABS_PATH, "icons", "loader_icon.png")
        deleter_icon_path = os.path.join(self.PLUGIN_ABS_PATH, "icons", "deleter_icon.png")
        admin_icon_path   = os.path.join(self.PLUGIN_ABS_PATH, "icons", "admin_icon.png")

        # Loader Dialog
        self.add_action(
            icon_path = loader_icon_path,
            #txt = self.tr(self.PLUGIN_NAME_LOADER),
            txt = self.PLUGIN_NAME_LOADER,
            callback = self.run_loader,
            parent = self.iface.mainWindow(),
            add_to_menu = True,
            add_to_toolbar = True) # Default: True

        # Deleter Dialog
        self.add_action(
            icon_path = deleter_icon_path,
            #txt = self.tr(self.PLUGIN_NAME_DELETER),
            txt = self.PLUGIN_NAME_DELETER,
            callback = self.run_deleter,
            parent = self.iface.mainWindow(),
            add_to_menu = True,
            add_to_toolbar = True) # Default: True

        # Admin Dialog
        self.add_action(
            icon_path = admin_icon_path,
            #txt = self.tr(self.PLUGIN_NAME_ADMIN),
            txt = self.PLUGIN_NAME_ADMIN,
            callback = self.run_admin,
            parent = self.iface.mainWindow(),
            add_to_menu = True,
            add_to_toolbar = True) # Default: False (but useful to set it to True in development mode).

        # Will be set False in run_admin(), run_loader(), run_deleter() etc.
        self.first_start_loader = True
        self.first_start_deleter = True
        self.first_start_admin = True


    def unload(self) -> None:
        """Removes the plugin menu item and icon from QGIS GUI.
        """
        for action in self.actions:
            self.iface.removeDatabaseToolBarIcon(qAction=action)
            self.iface.removePluginDatabaseMenu(name=self.PLUGIN_NAME, action=action)


    def run_loader(self) -> None:
        """Run method that performs all the real work.
        -   Creates the plugin dialog
        -   Instantiates the plugin main class (CDB4LoaderDialog) with its GUI
        -   Sets up the plugin signals
        -   Executes the dialog
        """
        from .cdb4.gui_loader.loader_dialog import CDB4LoaderDialog # Loader dialog
        from .cdb4.gui_db_connector.functions import conn_functions as conn_f

        # Only create GUI ONCE in callback,
        # so that it will only load when the plugin is started.
        if self.first_start_loader:
            self.first_start_loader = False

            # Create the dialog with elements (after translation).
            self.loader_dlg = CDB4LoaderDialog(cdbMain=self)

            dlg = self.loader_dlg

            # Replace empty graphics view widget with Map canvas.
            dlg.gLayoutBasemap.replaceWidget(dlg.gvCanvas, dlg.CANVAS)
            dlg.vLayoutBasemapL.replaceWidget(dlg.gvCanvasL, dlg.CANVAS_L)

            # Remove empty graphics View widget from dialog.
            dlg.gvCanvas.setParent(None)
            dlg.gvCanvasL.setParent(None)

            # Get existing connections from QGIS profile settings.
            # They are added to the combo box (cbxExistingConn), and 
            # an event is fired (dlg.evt_cbxExistingConn_changed())
            conn_f.get_qgis_postgres_conn_list(dlg)

        # if not self.first_start_loader:
        #     if self.loader_dlg.conn != self.loader_dlg.prev_conn:
        #         # print ('loader gotcha!!')
        #         if self.loader_dlg.conn:
        #             self.loader_dlg.conn.close()
        #         self.loader_dlg.conn = None
        #         self.loader_dlg.DB = None
        #         conn_f.get_qgis_postgres_conn_list(self.loader_dlg)

        # Set the window modality.
        # Desired mode: When this dialogue is open, inputs in any other windows are blocked.
        # self.loader_dlg.setWindowModality(Qt.ApplicationModal) # i.e. 0, The window blocks input to other windows.
        self.loader_dlg.setWindowModality(Qt.NonModal) # i.e. 0, The window does not block input to other windows (for development purposes).

        # Show the dialog
        self.loader_dlg.show()

        # Run the dialog event loop.
        res = self.loader_dlg.exec_()

        if not res: # Dialog has been closed (X button was pressed)
            # Unlike with the admin Dialog, do not reset the GUI: the user may reopen it and use the same settings
            # self.loader_dlg.prev_conn = self.loader_dlg.conn
            # self.loader_dlg.prev_DB = self.loader_dlg.DB
            pass

        return None


    def run_deleter(self) -> None:
        """Run method that performs all the real work.
        -   Creates the plugin dialog
        -   Instantiates the plugin main class (CDB4DeleterDialog) with its GUI
        -   Sets up the plugin signals
        -   Executes the dialog
        """
        from .cdb4.gui_deleter.deleter_dialog import CDB4DeleterDialog # Deleter dialog
        from .cdb4.gui_db_connector.functions import conn_functions as conn_f        

        # Only create GUI ONCE in callback, so that it will only load when the plugin is started.
        if self.first_start_deleter:
            self.first_start_deleter = False

            # Create the dialog with elements (after translation).
            self.deleter_dlg = CDB4DeleterDialog(cdbMain=self)

            dlg = self.deleter_dlg

            # Replace empty graphics view widget with Map canvas.
            dlg.gLayoutBasemap.replaceWidget(dlg.gvCanvas, dlg.CANVAS)

            # Remove empty graphics View widget from dialog.
            dlg.gvCanvas.setParent(None)

            # Get existing connections from QGIS profile settings.
            # They are added to the combo box (cbxExistingConn), and 
            # an event is fired (dlg.evt_cbxExistingConn_changed())
            conn_f.get_qgis_postgres_conn_list(dlg) # Stored in self.conn

        # if not self.first_start_deleter:
        #     if self.deleter_dlg.conn != self.deleter_dlg.prev_conn:
        #         # print ('deleter: gotcha!!')
        #         if self.deleter_dlg.conn:
        #             self.deleter_dlg.conn.close()
        #         self.deleter_dlg.conn = None
        #         self.deleter_dlg.DB = None
        #         conn_f.get_qgis_postgres_conn_list(self.deleter_dlg)

        # Set the window modality.
        # Desired mode: When this dialogue is open, inputs in any other windows are blocked.
        # self.deleter_dlg.setWindowModality(Qt.ApplicationModal) # The window blocks input from other windows.
        self.deleter_dlg.setWindowModality(Qt.NonModal) # i.e. 0, The window does not block input to other windows (for development purposes).

        # Show the dialog
        self.deleter_dlg.show()

        # Run the dialog event loop.
        res = self.deleter_dlg.exec_() 
        if not res: # Dialog has been closed (X button was pressed)
            # Unlike with the admin Dialog, do not reset the GUI: the user may reopen it and use the same settings
            # self.deleter_dlg.prev_conn = self.deleter_dlg.conn
            # self.deleter_dlg.prev_DB = self.deleter_dlg.DB
            pass
        
        return None


    def run_admin(self) -> None:
        """Run method that performs all the real work.
        -   Creates the plugin dialog
        -   Instantiates the plugin main class (CDB4AdminDialog) with its GUI
        -   Sets up the plugin signals
        -   Executes the dialog
        """
        from .cdb4.gui_admin.admin_dialog import CDB4AdminDialog # Admin dialog
        from .cdb4.gui_admin.functions import tab_install_widget_functions as admin_ti_wf
        from .cdb4.gui_db_connector.functions import conn_functions as conn_f

        # Only create GUI ONCE in callback, so that it will only load when the plugin is started.
        if self.first_start_admin:
            self.first_start_admin = False
            # Create the dialog with elements (after translation).
            self.admin_dlg = CDB4AdminDialog(cdbMain=self)


        # Get existing connections from QGIS profile settings.
        # They are added to the combo box (cbxExistingConn), and 
        # an event is fired (dlg.evt_cbxExistingConn_changed())
        conn_f.get_qgis_postgres_conn_list(self.admin_dlg) # Stored in self.conn

        # Set the window modality.
        # Desired mode: When this dialogue is open, inputs in any other windows are blocked.
        # self.admin_dlg.setWindowModality(Qt.ApplicationModal) # i.e The window is modal to the application and blocks input to all windows.
        self.admin_dlg.setWindowModality(Qt.NonModal) # i.e. 0, The window does not block input to other windows (for development purposes).

        # Show the dialog
        self.admin_dlg.show()

        # Run the dialog event loop.
        res = self.admin_dlg.exec_()
      
        if not res: # Dialog has been closed (X button was pressed)
            # Reset the dialog widgets. (Closes the current open connection.)
            admin_ti_wf.tabInstall_reset(self.admin_dlg)
            if self.admin_dlg.conn:
                self.admin_dlg.conn.close()

        return None


    # def create_progress_bar(self, dlg: QDialog, layout: QVBoxLayout, position: int) -> None:
    #     """Function that creates a QProgressBar embedded into a QgsMessageBar, in a specific position in the GUI.

    #     *   :param layout: QLayout of the gui where the bar is to be
    #             assigned.
    #         :type layout: QBoxLayout

    #     *   :param position: The place (index) in the layout to place
    #             the progress bar
    #         :type position: int
    #     """
    #     # Create QgsMessageBar instance.
    #     dlg.msg_bar = QgsMessageBar()

    #     # Add the message bar into the input layer and position.
    #     layout.insertWidget(position, dlg.msg_bar)

    #     # Create QProgressBar instance into QgsMessageBar.
    #     dlg.bar = QProgressBar(parent=dlg.msg_bar)

    #     # Setup progress bar.
    #     dlg.bar.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
    #     dlg.bar.setStyleSheet("text-align: left;")

    #     # Show progress bar in message bar.
    #     dlg.msg_bar.pushWidget(dlg.bar, Qgis.Info)


    # def evt_update_bar(self, dialog_name: str, step: int, text: str) -> None:
    # # def evt_update_bar(self, dlg_progress_bar: QProgressBar, step: int, text: str) -> None:
    #     """Function to setup the progress bar upon update. Important: Progress Bar needs to be already created
    #     in cdbMain.msg_bar: QgsMessageBar and cdbMain.bar: QProgressBar.
    #     This event is not linked to any widet_setup function as it isn't responsible for changes in different 
    #     widgets in the gui.

    #     *   :param dialog: The dialog to hold the bar.
    #         e.g. "admin_dlg" or "loader_dlg"
    #         :type step: str

    #     *   :param step: Current value of the progress
    #         :type step: int

    #     *   :param text: Text to display on the bar
    #         :type text: str
    #     """
    #     if dialog_name == self.DLG_NAME_ADMIN:         # "admin_dlg"
    #         progress_bar = self.admin_dlg.bar
    #     elif dialog_name == self.DLG_NAME_LOADER:      # "loader_dlg":
    #         progress_bar = self.loader_dlg.bar
    #     elif dialog_name == self.DLG_NAME_DELETER:     # "deleter_dlg":
    #         progress_bar = self.deleter_dlg.bar

    #     # Show text instead of completed percentage.
    #     if text:
    #         progress_bar.setFormat(text)

    #     # Update progress with current step
    #     progress_bar.setValue(step)