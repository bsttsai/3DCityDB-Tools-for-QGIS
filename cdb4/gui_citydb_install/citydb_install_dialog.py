"""
/***************************************************************************
Class CityDBInstallDialog

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
import os
import psycopg2
from psycopg2.extensions import connection as pyconn
import subprocess

from qgis.core import Qgis, QgsSettings
from qgis.gui import QgsMessageBar
from qgis.PyQt import QtWidgets, uic

from .citydb_install_dialog_constants import *
from .functions import install_setup as inst
from ..shared.functions import general_functions as gen_f


FILE_LOCATION = gen_f.get_file_relative_path(__file__)

# This loads the .ui file so that PyQt can populate the plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "db_citydb_installation.ui"))

class CityDBInstallDialog(QtWidgets.QDialog, FORM_CLASS):
    """3DCityDB installation Dialog. This dialog pops up when a user requests to install the 3DCityDB v4.1.0 from the plugin.
    """
    def __init__(self,currCon, parent=None):
        super(CityDBInstallDialog, self).__init__(parent)

        self.setupUi(self)

        ############################################################
        ## From here you can add your variables or constants
        ############################################################

        self.currentConnection = currCon
        if self.currentConnection: # Set current connection's credentials ONLY if it exists 
            self.ledHost.setText(self.currentConnection.host)
            self.ledPort.setText(self.currentConnection.port)
            self.ledDb.setText(self.currentConnection.database_name)
            self.ledUserName.setText(self.currentConnection.username)

        # Extract the LinedEdit parent widget of the QgsFileWidget
        self.ledFileAPIpath = self.fileAPIpath.lineEdit()

        # Put some placeholder text to help the user get the idea of what/where the required input is.
        if gen_f.on_unix():
            self.ledFileAPIpath.setPlaceholderText(PSQL_PROBABLE_PATH_UNIX)
        if gen_f.on_windows():
            self.ledFileAPIpath.setPlaceholderText(PSQL_PROBABLE_PATH_WIN)

        ### SIGNALS (start) ############################

        # Connect signals
        self.btnOK.clicked.connect(self.evt_btnOK_clicked)
        self.btnCancel.clicked.connect(self.evt_btnCancel_clicked)

        ### SIGNALS (end) ##############################

        ################################################
        ### EVENTS (start) ############################


    def evt_btnOK_clicked(self) -> None:
        """Event that is called when the 'OK' pushButton (btnOK) is pressed. It checks the connection,
        and, if successful, 
        """

        # Get PostgreSQL API executable file path from input
        psql_path = self.fileAPIpath.filePath()

        if gen_f.on_windows():
            print("Running on windows")
            inst.setup_connection_file_win(db=self.currentConnection, psql_path=psql_path)

            # Change current working directory for the scipt chain to work
            os.chdir(CITYDB_DIR_Shell_SCRIPTS_UNIX) 

            # Command to execute CREATE_DB.bat in a new command prompt window
            command = f'start cmd /k "{CITYDB_Shell_SCRIPTS_DB_WIN}"'

            # Run the command in a new command prompt window
            subprocess.run(command, shell=True)

            self.close()

        
        if gen_f.on_unix():
            print("Running on unix")
            inst.setup_connection_file_unix(db=self.currentConnection, psql_path=psql_path)

            #From https://3dcitydb-docs.readthedocs.io/en/latest/first-steps/setup-3dcitydb.html
            # Make allow scripts to be executed by the current owner of the script
            inst.setup_permissions_unix()
            
            # Change current working directory for the scipt chain to work
            os.chdir(CITYDB_DIR_Shell_SCRIPTS_UNIX)

            # Command to execute CREATE_DB.sh in a new command prompt window
            command = f"gnome-terminal -- /bin/bash -c '{CITYDB_Shell_SCRIPTS_DB_UNIX}; exec /bin/bash'"
            # Run the command in a new terminal window
            subprocess.run(command, shell=True)

            self.close()

        

    def evt_btnCancel_clicked(self) -> None:
        """Event that is called when the 'Cancel' pushButton (btnCancel) is pressed.
        It simply closes the dialog.
        """
        self.close()

        ### EVENTS (end) ############################
        ################################################