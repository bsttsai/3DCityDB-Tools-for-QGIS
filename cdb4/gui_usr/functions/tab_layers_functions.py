"""This module contains functions that relate to the 'Import Tab'
(in the GUI look for the plugin logo).

These functions are usually called from widget_setup functions
relating to child widgets of the 'Import Tab'.
"""

from collections import OrderedDict

from qgis.core import (QgsProject, QgsMessageLog, QgsEditorWidgetSetup, 
                        QgsVectorLayer, QgsDataSourceUri, QgsAttributeEditorElement,
                        QgsAttributeEditorRelation, Qgis,QgsLayerTreeGroup,
                        QgsRelation,QgsAttributeEditorContainer)
from qgis.gui import QgsCheckableComboBox

from ....cdb_loader import CDBLoader # Used only to add the type of the function parameters
from ... import cdb4_constants as c
from . import sql

def has_matviews(cdbLoader: CDBLoader) -> bool:
    """Function that checks the existence of materialised
    views in the database.

    *   :returns: Whether the database has populated mat views.

        :rtype: bool
    """
    # Get materialised views names.
    mat_views = sql.fetch_mat_views(cdbLoader)

    # Check if materialised views names exist.
    if mat_views:
        return True
    return False

def fill_FeatureType_box(cdbLoader: CDBLoader) -> None:
    """Function that fills out the 'Feature Types' combo box.
    Uses the 'layer_metadata' table in usr_schema to instantiate
    useful python objects
    class: FeatureType and
    class: View
    """
    # Create 'Feature Type' and 'View' objects
    instantiate_objects(cdbLoader)

    # Add only those Feature Types that have at least
    # one view containing > 0 features.
    for FeatureType_obj in cdbLoader.FeatureType_container.values():
        for view in FeatureType_obj.views:
            if view.n_selected > 0:
                cdbLoader.usr_dlg.cbxFeatureType.addItem(FeatureType_obj.alias,FeatureType_obj)
                # The first FeatureType object added in 'cbxFeatureType' emits
                # a 'currentIndexChanged' signal.
                break # We need only one view to have > 0 features.

def instantiate_objects(cdbLoader: CDBLoader) -> None:
    """Function to instantiate python objects from the 'layer_metadata'
    table in the usr_schema.
    class: FeatureType and
    class: View
    """
    # Get field names and metadata values from server.
    colnames, metadata = sql.fetch_layer_metadata(cdbLoader, cdbLoader.USR_SCHEMA, cdbLoader.CDB_SCHEMA)
    # Format metadata into a list of dictionaries where each element is a layer.
    metadata_dict_list = [dict(zip(colnames, values)) for values in metadata]

    # Instantiate 'FeatureType' objects for each CityGML module
    # into a plugin variable (dict).
    cdbLoader.FeatureType_container = {
        "Bridge": c.FeatureType(alias="Bridge"),
        "Building": c.FeatureType(alias="Building"),
        "CityFurniture": c.FeatureType(alias="CityFurniture"),
        "Generics": c.FeatureType(alias="Generics"),
        "LandUse": c.FeatureType(alias="LandUse"),
        "Relief": c.FeatureType(alias="Relief"),
        "Transportation": c.FeatureType(alias="Transportation"),
        "Tunnel": c.FeatureType(alias="Tunnel"),
        "Vegetation": c.FeatureType(alias="Vegetation"),
        "WaterBody": c.FeatureType(alias="WaterBody")
        }

    for metadata_dict in metadata_dict_list:
        #keys:  id,cdb_schema,feature_type,lod,root_class,layer_name,n_features,mv_name, v_name,qml_file,creation_data,refresh_date
        if metadata_dict["n_features"] == 0:
            continue
        if metadata_dict["refresh_date"] is None:
            continue

        # Get the FeatureType object that the current layer is.
        curr_FeatureType_obj = cdbLoader.FeatureType_container[metadata_dict['feature_type']]

        # Create a View object with all the values extracted from 'layer_metadata'.
        view = c.View(*metadata_dict.values())

        # Add the view to the FeatureObject views list
        curr_FeatureType_obj.views.append(view)

        # Count the number of features that the view has in the current extents.
        sql.exec_view_counter(cdbLoader, view) # Stores number in view.n_selected.

def fill_lod_box(cdbLoader: CDBLoader) -> None:
    """Function that fills out the 'Geometry Level' combo box (LoD)."""

    # Get 'FeatureType' object from combo box data.
    selected_FeatureType = cdbLoader.usr_dlg.cbxFeatureType.currentData()
    if not selected_FeatureType:
        return None

    geom_set = set() # To store the unique lods.
    for view in selected_FeatureType.views:
        geom_set.add(view.lod)

    # Add lod string into both text and data holder of combo box.
    for lod in sorted(list(geom_set)):
        cdbLoader.usr_dlg.cbxLod.addItem(lod, lod)
        # The first LoD string added in 'cbxLod' emits
        # a 'currentIndexChanged' signal.

def fill_features_box(cdbLoader: CDBLoader) -> None:
    """Function that fills the 'Features' checkable combo box."""
    # Variable to store the plugin main dialog.
    dlg = cdbLoader.usr_dlg

    # Get current 'LoD' from widget.
    selected_lod = dlg.cbxLod.currentText()
    # Get current 'Feature Type' from widget.
    selected_FeatureType = dlg.cbxFeatureType.currentData()

    if not selected_FeatureType or not selected_lod:
        return None

    for view in selected_FeatureType.views:
        if view.lod == selected_lod:
            if view.n_selected > 0:
                dlg.ccbxFeatures.addItemWithCheckState(
                    text=f'{view.layer_name} ({view.n_selected})',
                    state=0,
                    userData=view)
    # TODO: 05-02-2021 Add separator between different features
    # REMEMBER: don't use method 'setSeparator',
    # it adds a custom separator to join string of selected items


def value_rel_widget(
        AllowMulti: bool = False,
        AllowNull: bool = True,
        FilterExpression: str = "",
        Layer: str = "",
        Key: str = "",
        Value: str = "",
        NofColumns: int = 1,
        OrderByValue: bool = False,
        UseCompleter: bool = False) -> QgsEditorWidgetSetup:
    """Function to setup the configuration dictionary for
    the 'Value Relation' widget.

    .. Note:this function could probably be generalized for all available
    ..      widgets of 'attribute from', but there is not need for this yet.

    *   :returns: The object to setup the widget (ValueRelation)

        :rtype: QgsEditorWidgetSetup
    """
    config = {'AllowMulti': AllowMulti,
              'AllowNull': AllowNull,
              'FilterExpression':FilterExpression,
              'Layer': Layer,
              'Key': Key,
              'Value': Value,
              'NofColumns': NofColumns,
              'OrderByValue': OrderByValue,
              'UseCompleter': UseCompleter}
    return QgsEditorWidgetSetup(type='ValueRelation', config=config)


def get_attForm_child(container: QgsAttributeEditorContainer, child_name: str) -> QgsAttributeEditorElement:
    """Function that searches to retrieve a child object from
    an 'attribute form' container.

    *   :param container: An attribute form container object.
        :type container: QgsAttributeEditorContainer

    *   :param child_name: The name of the child to be found.
        :type child_name: str

    *   :returns: The 'attribute form' child element (when found)
        :type child_name: QgsAttributeEditorElement | None
    """
    for child in container.children():
        if child.name() == child_name:
            return child
    return None


def create_lookup_relations(cdbLoader: CDBLoader, layer: QgsVectorLayer) -> None:
    """Function that sets-up the ValueRelation widget
    for the look-up tables.

    .. Note: Currently the look-up table names are hardcoded.
    .. Additionally enumeration ids for relative to water
    .. or terrain are also hardcoded.

    *   :param layer: Layer to search for and set-up its
            'Value Relation' widget according to the look-up tables.

        :type layer: QgsVectorLayer

    .. The problem of codelists is too dynamic to be solved by this function.
    """
    for field in layer.fields():
        field_name = field.name()
        field_idx = layer.fields().indexOf(field_name)

        assertion_msg = "ValueRelation Error: layer '{}' doesn\'t exist in project. This layers is also being imported with every layer import (if it doesn\'t already exist)."

        # Isolate the layers' ToC environment to avoid grabbing the first layer encountered in the WHOLE ToC.
        root = QgsProject.instance().layerTreeRoot()
        db_node = root.findGroup(cdbLoader.DB.database_name)
        schema_node = db_node.findGroup("@".join([cdbLoader.DB.username,cdbLoader.CDB_SCHEMA]))
        look_node = schema_node.findGroup("Look-up tables")
        look_layers = look_node.findLayers()
        enum_layer_id = [i.layerId() for i in look_layers if c.enumerations_table in i.layerId()][0]

        if field_name == 'relative_to_terrain':
            assert enum_layer_id, assertion_msg.format(f'{cdbLoader.CDB_SCHEMA}_v_enumeration_value')
            layer.setEditorWidgetSetup(field_idx, value_rel_widget(Layer= enum_layer_id, Key='value', 
                Value='description', FilterExpression="data_model = 'CityGML 2.0' AND name = 'RelativeToTerrainType'"))

        elif field_name == 'relative_to_water':
            assert enum_layer_id, assertion_msg.format(f'{cdbLoader.CDB_SCHEMA}_v_enumeration_value')
            layer.setEditorWidgetSetup(field_idx, value_rel_widget(Layer= enum_layer_id, Key='value', 
                Value='description', FilterExpression="data_model = 'CityGML 2.0' AND name = 'RelativeToWaterType'"))



def create_relations(cdbLoader: CDBLoader, layer: QgsVectorLayer) -> None:
    """Function to set-up the relation for an input layer.
    - A new relation is created that references the generic attributes.
    - Relations are also set for 'Value Relation' widget.

    .. Note:Currently relations are created ONLY for specific hardcode lookup
    ..      tables and the Generic Attributes. In the future we need to make
    ..      space for 'addresses' and other.

    *   :param layer: vector layer to set up the relationships for.

        :type layer: QgsVectorLayer
    """
    layer_configuration = layer.editFormConfig()
    layer_root_container = layer_configuration.invisibleRootContainer()

    # Isolate the layers' ToC environment to avoid grabbing the first layer encountered in the WHOLE ToC.
    root = QgsProject.instance().layerTreeRoot()
    db_node = root.findGroup(cdbLoader.DB.database_name)
    schema_node = db_node.findGroup("@".join([cdbLoader.DB.username,cdbLoader.CDB_SCHEMA]))
    generics_node = schema_node.findGroup("Generic Attributes")
    genericAtt_layer = generics_node.findLayers()[0]

    assert genericAtt_layer, "generic_attributes table doesn\'t exist in project."

    # Generic Attributes relation.
    # Create new relation object (referencing generic attributes)
    rel = QgsRelation()
    rel.setReferencedLayer(id=layer.id())
    rel.setReferencingLayer(id=genericAtt_layer.layerId())
    rel.addFieldPair(referencingField='cityobject_id', referencedField='id')
    rel.generateId()
    rel.setName('re_' + layer.name())
    rel.setStrength(0)
    if rel.isValid(): # Success
        QgsProject.instance().relationManager().addRelation(rel)
        QgsMessageLog.logMessage(
            message=f"Create relation: {rel.name()}",
            tag="3DCityDB-Loader",
            level=Qgis.Success,
            notifyUser=True)
    else:
        QgsMessageLog.logMessage(
            message=f"Invalid relation: {rel.name()}",
            tag="3DCityDB-Loader",
            level=Qgis.Critical,
            notifyUser=True)

    # Find and store 'Generic Attributes' 'attribute form' element.
    container_GA = get_attForm_child(container=layer_root_container, child_name='Generic Attributes')
    # Clean the element before inserting the relation
    container_GA.clear()

    # Create an 'attribute form' relation object from the 'relation' object
    relation_field = QgsAttributeEditorRelation(relation=rel, parent=container_GA)
    relation_field.setLabel("Generic Attributes")
    relation_field.setShowLabel(False) # No point setting a label then.
    # Add the relation to the 'Generic Attributes' container (tab).
    container_GA.addChildElement(relation_field)

    # Commit?
    layer.setEditFormConfig(layer_configuration)

    # Look-up tables relation
    create_lookup_relations(cdbLoader, layer)


def group_has_layer(group: QgsLayerTreeGroup, layer_name: str) -> bool:
    """Function that checks whether a specific group
    has a specific underlying layer (by name).
    *   :param group: Node object to check for layer existence.
        :type group: QgsLayerTreeGroup
    *   :param layer_name: Layer name to check if it exists.
        :type layer_name: str
    *   :returns: Search result.
        :rtype: bool
    """
    if layer_name in [child.name() for child in group.children()]:
        return True
    return False


def import_lookups(cdbLoader: CDBLoader) -> None:
    """Function to import the look-up table into the qgis project."""

    # Add look-up tables into their own group in ToC.
    root = QgsProject.instance().layerTreeRoot().findGroup("@".join([cdbLoader.DB.username,cdbLoader.CDB_SCHEMA]))
    lookups_node = add_node_ToC(parent_node=root, child_name="Look-up tables")

    # Get look-up tables names from the server.
    lookups = sql.fetch_lookup_tables(cdbLoader)

    # Connected database. Just to shorten the variable name.
    db = cdbLoader.DB

    for table in lookups:
        # Create ONLY new layers.
        if not group_has_layer(group=lookups_node, layer_name=table):
            uri = QgsDataSourceUri()
            uri.setConnection(db.host, db.port, db.database_name, db.username, db.password)
            uri.setDataSource(aSchema=cdbLoader.USR_SCHEMA, aTable=table, aGeometryColumn=None, aKeyColumn="id")
            layer = QgsVectorLayer(uri.uri(False), f"{cdbLoader.CDB_SCHEMA}_{table}", "postgres")
            if layer or layer.isValid(): # Success
                lookups_node.addLayer(layer)
                QgsProject.instance().addMapLayer(layer, False)
                QgsMessageLog.logMessage(
                    message=f"Look-up table import: {cdbLoader.CDB_SCHEMA}_{table}",
                    tag="3DCityDB-Loader",
                    level=Qgis.Success, notifyUser=True)
            else: # Fail
                QgsMessageLog.logMessage(
                    message=f"Look-up table failed to properly load: {cdbLoader.CDB_SCHEMA}_{table}",
                    tag="3DCityDB-Loader",
                    level=Qgis.Critical, notifyUser=True)

    # After loading all look-ups, sort them by name.
    sort_ToC(lookups_node)


def import_generics(cdbLoader: CDBLoader) -> None:
    """Function to import the 'generic attributes' into the qgis project."""
    # Just to shorten the variables names.
    db = cdbLoader.DB
    cdb_schema = cdbLoader.CDB_SCHEMA

    # Add generics tables into their own group in ToC.
    root = QgsProject.instance().layerTreeRoot().findGroup("@".join([db.username, cdb_schema]))
    generics_node = add_node_ToC(parent_node=root, child_name=c.generics_alias)


    # Add it ONLY if it doesn't already exists.
    if not group_has_layer(generics_node, f"{cdbLoader.CDB_SCHEMA}_{c.generics_table}"):
        uri = QgsDataSourceUri()
        uri.setConnection(db.host, db.port, db.database_name, db.username, db.password)
        uri.setDataSource(aSchema=cdb_schema,
            aTable=c.generics_table,
            aGeometryColumn=None,
            aKeyColumn="")
        layer = QgsVectorLayer(uri.uri(False), f"{cdbLoader.CDB_SCHEMA}_{c.generics_table}", "postgres")
        if layer or layer.isValid(): # Success
            # NOTE: Force cityobject_id to Text Edit (relation widget, automatically set by qgis)
            # WARNING: hardcoded index (15: cityobject_id)
            layer.setEditorWidgetSetup(15, QgsEditorWidgetSetup('TextEdit',{}))

            generics_node.addLayer(layer)
            QgsProject.instance().addMapLayer(layer, False)

            QgsMessageLog.logMessage(
                message=f"Layer import: {cdbLoader.CDB_SCHEMA}_{c.generics_table}",
                tag="3DCityDB-Loader",
                level=Qgis.Success,
                notifyUser=True)
        else:
            QgsMessageLog.logMessage(
                message=f"Layer failed to properly load: {cdbLoader.CDB_SCHEMA}_{c.generics_table}",
                tag="3DCityDB-Loader",
                level=Qgis.Critical,
                notifyUser=True)


def create_layers(cdbLoader: CDBLoader, v_name: str) -> QgsVectorLayer:
    """Function that creates a postgres layer of a server table
    based on the input view name. This function is used to import
    updatable views from qgis_pkg queried to the selecte spatial
    extents.

    *   :param v_name: View name to connect to server.

        :type v_name: str

    *   :returns: the created layer object

        :rtype: QgsVectorLayer
    """

    #Just to shorten the variable names.
    db = cdbLoader.DB
    usr_schema = cdbLoader.USR_SCHEMA
    extents = cdbLoader.QGIS_EXTENTS.asWktPolygon()
    crs = cdbLoader.CRS

    uri = QgsDataSourceUri()
    uri.setConnection(db.host, db.port, db.database_name, db.username, db.password)
    uri.setDataSource(aSchema=usr_schema,
        aTable=v_name,
        aGeometryColumn=c.geom_col,
        aSql=f"ST_GeomFromText('{extents}') && {c.geom_col}",
        aKeyColumn=c.id_col)
    vlayer = QgsVectorLayer(uri.uri(False), v_name, "postgres")
    vlayer.setCrs(crs)

    return vlayer

#NOTE: this function could be generalized to
# accept ToC index location as a parameter (int).
def send_to_top_ToC(group: QgsLayerTreeGroup) -> None: 
    """Function that send the input group to the top
    of the project's 'Table of Contents' tree.
    """
    # According to qgis docs, this is the prefered way.
    root = QgsProject.instance().layerTreeRoot()
    move_group =  group.clone()
    root.insertChildNode(0, move_group)
    root.removeChildNode(group)

#NOTE: this function could be generalized to 
# accept ToC index location as a parameter (int).
def send_to_bottom_ToC(node: QgsLayerTreeGroup) -> None:
    """Function that send the input group to the bottom
    of the project's 'Table of Contents' tree.

    """
    group= None
    names = [ch.name() for ch in node.children()]
    if 'FeatureType: Relief' in names:

        for c,i in enumerate(node.children()):

            if 'FeatureType: Relief' == i.name():
                group = i
                break
        if group:
            idx=len(node.children())-2

            move_group =  group.clone()
            node.insertChildNode(idx, move_group)
            node.removeChildNode(group)

        return None
    
    for child in node.children():
        send_to_bottom_ToC(child)


def get_node_database(cdbLoader: CDBLoader) -> QgsLayerTreeGroup:
    """Function that finds the database node of the
    project's 'Table of Contents' tree (by name).

    *   :returns: database node (qgis group)

        :rtype: QgsLayerTreeGroup
    """

    root = QgsProject.instance().layerTreeRoot()
    db_node = root.findGroup(cdbLoader.DB.database_name)
    return db_node


def sort_ToC(group: QgsLayerTreeGroup) -> None:
    """Recursive function to sort the entire 'Table of Contents' tree,
    including both groups and underlying layers.
    """

    # Germán Carrillo: https://gis.stackexchange.com/questions/397789/sorting-layers-by-name-in-one-specific-group-of-qgis-layer-tree #
    LayerNamesEnumDict=lambda listCh:{listCh[q[0]].name()+str(q[0]):q[1] for q in enumerate(listCh)}

    # group instead of root
    mLNED = LayerNamesEnumDict(group.children())
    mLNEDkeys = OrderedDict(sorted(LayerNamesEnumDict(group.children()).items(), reverse=False)).keys()

    mLNEDsorted = [mLNED[k].clone() for k in mLNEDkeys]
    group.insertChildNodes(0,mLNEDsorted)  # group instead of root
    for n in mLNED.values():
        group.removeChildNode(n)  # group instead of root
    # Germán Carrillo #

    group.setExpanded(True)
    for child in group.children():
        if isinstance(child, QgsLayerTreeGroup):
            sort_ToC(child)
        else: return None
    return None


def add_node_ToC(
        parent_node: QgsLayerTreeGroup,
        child_name: str) -> QgsLayerTreeGroup:
    """Function that adds a node (group) into the qgis
    project 'Table of Contents' tree (by name). It also checks
    if the node already exists and returns it.

    *   :param parent_node: A node on which the new node is going to be added
            (or returned if it already exists).

        :type parent_node: QgsLayerTreeGroup

    *   :param child_name: A string name of the new or existing node (group).

        :type child_name: str

    *   :returns: The newly created node object (or the existing one).

        :rtype: QgsLayerTreeGroup
    """

    # node_name group (e.g. test_db)
    if not parent_node.findGroup(child_name):
        # Create group
        node = parent_node.addGroup(child_name)
    else:
        # Get existing group
        node = parent_node.findGroup(child_name)
    return node


def build_ToC(cdbLoader: CDBLoader, view: c.View) -> QgsLayerTreeGroup:
    """Function that building the project's 'Table of Contents' tree.

    *   :param view: The view used to build the ToC.

        :type view: View

    *   :returns: The node (group) where the view is going to occupy.

        :rtype: QgsLayerTreeGroup
    """

    root = QgsProject.instance().layerTreeRoot()

    # Database group (e.g. test_db)
    db_node = add_node_ToC(parent_node=root,
        child_name=cdbLoader.DB.database_name)

    # Schema group (e.g. citydb)
    node_schema = add_node_ToC(parent_node=db_node,
        child_name="@".join([cdbLoader.DB.username, view.cdb_schema]))

    # FeatureType group (e.g. Building)
    node_FeatureType = add_node_ToC(parent_node=node_schema,
        child_name=f"FeatureType: {view.feature_type}")

    # Feature group (e.g. Building Part)
    node_feature = add_node_ToC(parent_node=node_FeatureType,
        child_name=view.root_class)

    # LoD group (e.g. lod2)
    node_lod = add_node_ToC(parent_node=node_feature,
        child_name=view.lod)

    return node_lod # Not where the view is going to be inserted.


def get_checkedItemsData(ccbx: QgsCheckableComboBox) -> list:
    """Function to extract the QVariant data from a
    QgsCheckableComboBox widget.

    Replaces built-in method: checkedItemsData()
    """

    checked_items = []
    for idx in range(ccbx.count()):
        if ccbx.itemCheckState(idx) == 2: #is Checked
            checked_items.append(ccbx.itemData(idx))
    return checked_items


def import_layers(cdbLoader: CDBLoader, layers: list) -> bool:
    """Function to import the selected layer in the user's
    qgis project.

    *   :param layers: A list containing View object that
            correspond to the server views.

        :type layers: list(View)

    *   :returns: The import attempt result

        :rtype: bool
    """
    for view in layers:
        #Build the Table of Contents Tree or Restructure it.
        node = build_ToC(cdbLoader, view)

        # Get the look up tables.
        # While the function checks for existing lookups in the qgis project,
        # I think that is better to move this out of the loop.
        import_lookups(cdbLoader)
        vlayer = create_layers(cdbLoader, v_name=view.v_name)
        import_generics(cdbLoader)

        if vlayer or vlayer.isValid(): # Success
            QgsMessageLog.logMessage(
                message=f"Layer import: {view.v_name}",
                tag="3DCityDB-Loader",
                level=Qgis.Success,
                notifyUser=True)
        else: # Fail
            QgsMessageLog.logMessage(
                message=f"Layer failed to properly load: {view.v_name}",
                tag="3DCityDB-Loader",
                level=Qgis.Critical,
                notifyUser=True)
            return False

        # Insert the layer to the assigned group
        node.addLayer(vlayer)
        QgsProject.instance().addMapLayer(vlayer, False)

        # Attach 'attribute form' from QML file.
        vlayer.loadNamedStyle(view.qml_path)

        # Setup the relation for this layer.
        create_relations(cdbLoader, layer=vlayer)

        # Deactivate 3D renderer to avoid crashes.
        vlayer.setRenderer3D(None)

    return True # All went well
