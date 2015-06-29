# $Id: SpatialModelEditor.py,v 1.1.1.1.6.1 2014/04/16 14:53:55 tstephen Exp $

#******************************************************************************

# Import external modules.

# Standard modules
from tkFileDialog import Open
import Tkinter

# Third-party modules
import Pmw

# Project modules
from ElementEditor import ElementEditor
from Parameter import Parameter
from ParameterEditor import ParameterEditor
from SpatialModel import SpatialModel

#******************************************************************************

class SpatialModelEditor(ElementEditor):
    """Class to edit ModelEditor SpatialModel objects.

    Python implementation of the SpatialModelEditor class which allows
    the user to edit the fields of a <spatialModel> element. This
    compound widget is designed to be embedded in other widgets.

    Attributes:

    _typeOptionMenu: (Pmw.OptionMenu) For selecting the SpatialModel
    type.

    _fileEntryField: (Pmw.EntryField) For specifying a file associated
    with the SpatialModel.

    _fileBrowseButton: (Tkinter.Button) Summons a Open dialog to select
    a file for the fileEntryField.

    _parameterEditors: (ParameterEditor) List of ParameterEditor
    objects for individual Parameters.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Number of ParameterEditors to create
    _nParameterEditors = 7

    #--------------------------------------------------------------------------

    def __init__(self,
                 parent       = None,
                 spatialModel = None,
                 *args, **kwargs):
        """Initialize this SpatialModelEditor.

        Parameters:

        self: This object.

        parent: (Tkinter.Frame) Parent object for this widget.

        spectrum: (SpatialModel) SpatialModel to initialize fields.

        Return value:

        None.

        Description:

        Initialize this SpectrumEditor.
        """

        # Initialize the parent class (which calls _makeWidgets and
        # set for this class).
        if spatialModel is None:
            spatialModel = SpatialModel()
        ElementEditor.__init__(self, parent, spatialModel, *args, **kwargs)

    #--------------------------------------------------------------------------

    def _makeWidgets(self):
        """Build child widgets.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:

        Create all of the GUI widgets required by this object.
        """

        # Create any inherited widgets.
        ElementEditor._makeWidgets(self)

        # Create and grid a OptionMenu for the SpatialModel type.
        width = max([len(s) for s in SpatialModel._validTypes])
        optionMenu = Pmw.OptionMenu(self, items = \
                                    sorted(SpatialModel._validTypes),
                                    label_text = 'Spatial Model Type:',
                                    labelpos = 'w',
                                    menubutton_width = width,
                                    command = self._onSelectType)
        optionMenu.grid(row = 0, column = 0, sticky = 'w')
        self._typeOptionMenu = optionMenu
        self._balloon.bind(self._typeOptionMenu, 'Set the spatial model type.')

        # Create and grid an arbitrary string EntryField for the
        # SpatialModel file, and an accompanying button which summons
        # an Open dialog.
        entryField = Pmw.EntryField(self, labelpos = 'w', label_text = 'File:')
        entryField.grid(row = 0, column = 1, sticky = 'e')
        self._fileEntryField = entryField
        self._balloon.bind(self._fileEntryField,
                           'Enter the path to the file of data for this'\
                           ' spatial model.')
        button = Tkinter.Button(self, text = 'Browse', command = self.onBrowse)
        button.grid(row = 0, column = 2, sticky = 'e')
        self._fileBrowseButton = button
        self._balloon.bind(self._fileBrowseButton,
                           'Browse to the file of data for this spatial '\
                           'model.')

        # Create and grid a Frame for the set of ParameterEditors.
        frame = Tkinter.Frame(self)
        frame.grid(row = 1, column = 0, columnspan = 3, sticky = 'ew')

        # Create and grid a set of ParameterEditors.
        self._parameterEditors = []
        for row in range(SpatialModelEditor._nParameterEditors):
            if row == 0:
                showLabels = True
            else:
                showLabels = False
            parameterEditor = ParameterEditor(frame, showLabels = showLabels)
            parameterEditor.grid(row = row, column = 0, sticky = 'ew')
            self._parameterEditors.append(parameterEditor)

    #--------------------------------------------------------------------------

    def get(self):
        """Return the contents of the editor.

        Parameters:

        self: This object.

        Return value:

        Copy of SpatialModel being edited.

        Description:

        Return a new SpatialModel containing the current state of the
        editor.
        """

        # Fetch the type.
        type = self._typeOptionMenu.getvalue()

        # Fetch the file (mapping empty string to None).
        file = self._fileEntryField.getvalue()
        if file == '':
            file = None

        # Get the contents of each needed ParameterEditor.
        parameters = [parameterEditor.get() \
                      for parameterEditor in \
                      self._parameterEditors[:self._nActiveParameterEditors]]

        # Create the new SpatialModel.
        spatialModel = SpatialModel(type, file, parameters)

        # Return the new SpatialModel.
        return spatialModel

    def set(self, spatialModel):
        """Set the editor state.

        Parameters:

        self: This object.

        spatialModel: (SpatialModel): Object to set in this editor.

        Return value:

        None.

        Description:
        
        Set the fields using a SpatialModel.
        """

        # Set the type OptionMenu.
        type = spatialModel.getType()
        self._typeOptionMenu.setvalue(type)

        # Set the file field (mapping None to empty string).
        file = spatialModel.getFile()
        if file is None:
            file = ''
        self._fileEntryField.setvalue(file)
        if type == 'MapCubeFunction' or type == 'SpatialMap':
            self._fileEntryField.configure(entry_state = 'normal')
            self._fileBrowseButton.configure(state = 'normal')
        else:
            self._fileEntryField.configure(entry_state = 'disabled')
            self._fileBrowseButton.configure(state = 'disabled')

        # Initially clear and disable all ParameterEditors (to prevent
        # shadowing of old values).
        for parameterEditor in self._parameterEditors:
            parameterEditor.clear()
            parameterEditor.disable()

        # Use the current Parameters to fill in and enable the
        # required number of ParameterEditors.
        parameters = spatialModel.getParameters()
        i = 0
        for parameter in parameters:
            self._parameterEditors[i].enable()
            self._parameterEditors[i].set(parameter)
            i += 1
        self._nActiveParameterEditors = i

    #--------------------------------------------------------------------------

    def enable(self):
        """Activate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:

        Activate all of the child widgets in this SpatialModelEditor.
        """
        self._typeOptionMenu.configure(menubutton_state = 'normal')
        self._fileEntryField.configure(entry_state = 'normal')
        self._fileBrowseButton.configure(state = 'normal')
        for parameterEditor in self._parameterEditors:
            parameterEditor.enable()

    def disable(self):
        """Deactivate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:
        
        Deactivate all of the child widgets in this SpatialModelEditor.
        """
        self._typeOptionMenu.configure(menubutton_state = 'disabled')
        self._fileEntryField.configure(entry_state = 'disabled')
        self._fileBrowseButton.configure(state = 'disabled')
        for parameterEditor in self._parameterEditors:
            parameterEditor.disable()

    #--------------------------------------------------------------------------

    def _onSelectType(self, type):
        """Process selection events in the type list box.

        Parameters:

        self: This object.

        type: (string) New SpatialModel type string.

        Return value:

        None.

        Description:
        
        Process the selection of a new SpatialModel type in the type
        OptionMenu.
        """

        # If the new type is the same as the previous type, no change
        # is needed.
        if type == self._referenceElement.getType():
            return

        # A new SpatialModel type has been selected, so create a new
        # one.
        spatialModel = SpatialModel(type = type)

        # Set the editor with the new SpatialModel.
        self.set(spatialModel)
        self.commit()

    #--------------------------------------------------------------------------

    def onBrowse(self):
        """Present the File Open dialog.

        Parameters:

        self: This object.

        Return value:

        String containing the path to the selected file, or None if no
        file was selected.

        Description:

        Display the File/Open dialog box and return the path to the
        selected file.
        """

        # Present the file/open dialog.
        path = Open().show()

        # If no file was selected, return.
        if path == '':
            return

        # Save the current path in the file entry field.
        self._fileEntryField.setvalue(path)

    #--------------------------------------------------------------------------

    def setDS9Connector(self,connector):
        self._ds9Connector = connector
        #also pass down to the Parameter Editors
        for editor in self._parameterEditors:
            editor.setDS9Connector(connector)

        
#******************************************************************************

# Self-test code.
import xml.dom.minidom
domDocument = xml.dom.minidom.Document()

# Printing routine for buttons.
def _print(editor):
    print editor.get()
    if editor.getChanged():
        print "Changed by the editor."

# XML printing routine for buttons.
def _printXML(editor):
    element = editor.get()
    dom = element.toDom(domDocument)
    print dom.toxml()
    if editor.getChanged():
        print "Changed by the editor."

if __name__ == '__main__':

    # Create the root window.
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title('SpatialModelEditor test')

    # Create and grid an editor for a default SpatialModel, a button
    # to commit changes, and a button to dump its contents.
    spatialModelEditor = SpatialModelEditor()
    spatialModelEditor.grid(row = 0, column = 0)
    commitButton = Tkinter.Button(root, text = 'Commit',
                                  command = spatialModelEditor.commit)
    commitButton.grid(row = 0, column = 1)
    resetButton = Tkinter.Button(root, text = 'Reset',
                                  command = spatialModelEditor.reset)
    resetButton.grid(row = 0, column = 2)
    printButton = Tkinter.Button(root, text = 'Print',
                                 command = \
                                 lambda: _print(spatialModelEditor))
    printButton.grid(row = 0, column = 3)
    printXMLButton = Tkinter.Button(root, text = 'Print XML',
                                    command = \
                                    lambda: _printXML(spatialModelEditor))
    printXMLButton.grid(row = 0, column = 4)

    # Enter the main program loop.
    root.mainloop()
