# $Id: SpectrumEditor.py,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

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
from Spectrum import Spectrum

#******************************************************************************

class SpectrumEditor(ElementEditor):
    """Class to edit ModelEditor Spectrum objects.
    
    Python implementation of the SpectrumEditor class which allows the
    user to edit the fields of a <spectrum> element. This compound
    widget is designed to be embedded in other widgets.

    Attributes:

    _typeOptionMenu: (Pmw.OptionMenu) For selecting the Spectrum type.

    _fileEntryField: (Pmw.EntryField) For specifying a file associated
    with the Spectrum.

    _fileBrowseButton: (Tkinter.Button) Summons a Open dialog to
    select a file for the fileEntryField.

    _parameterEditors: (ParameterEditor) List of ParameterEditor
    objects for individual Parameters.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Number of ParameterEditors to create
    _nParameterEditors = 7

    #--------------------------------------------------------------------------

    def __init__(self,
                 parent   = None,
                 spectrum = None,
                 *args, **kwargs):
        """Initialize this SpectrumEditor.

        Parameters:

        self: This object.

        parent: (Tkinter.Frame) Parent object for this widget.

        spectrum: (Spectrum) Spectrum to initialize fields.

        Return value:

        None.

        Description:

        Initialize this SpectrumEditor.
        """

        # Initialize the parent class (which calls _makeWidgets and
        # set for this class).
        if spectrum is None:
            spectrum = Spectrum()
        ElementEditor.__init__(self, parent, spectrum, *args, **kwargs)

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

        # Create and grid a OptionMenu for the Spectrum type.
        width = max([len(s) for s in Spectrum._validTypes])
        optionMenu = Pmw.OptionMenu(self, items = sorted(Spectrum._validTypes),
                                    label_text = 'Spectrum Type:',
                                    labelpos = 'w',
                                    menubutton_width = width,
                                    command = self._onSelectType)
        optionMenu.grid(row = 0, column = 0, sticky = 'w')
        self._typeOptionMenu = optionMenu
        self._balloon.bind(self._typeOptionMenu, 'Set the spectrum type.')

        # Create and grid an arbitrary string EntryField for the
        # Spectrum file, and an accompanying button which summons an
        # Open dialog.
        entryField = Pmw.EntryField(self, labelpos = 'w', label_text = 'File:')
        entryField.grid(row = 0, column = 1, sticky = 'e')
        self._fileEntryField = entryField
        self._balloon.bind(self._fileEntryField,
                           'Enter the path to the file of data for this'\
                           ' spectrum.')
        button = Tkinter.Button(self, text = 'Browse', command = self.onBrowse)
        button.grid(row = 0, column = 2, sticky = 'e')
        self._fileBrowseButton = button
        self._balloon.bind(self._fileBrowseButton,
                           'Browse to the file of data for this spectrum.')

        # Create and grid a Frame for the set of ParameterEditors.
        frame = Tkinter.Frame(self)
        frame.grid(row = 1, column = 0, columnspan = 3, sticky = 'ew')

        # Create and grid a set of ParameterEditors.
        self._parameterEditors = []
        for row in range(SpectrumEditor._nParameterEditors):
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

        Copy of Spectrum being edited.

        Description:

        Return a new Spectrum containing the current state of the
        editor.
        """

        # Fetch the type.
        type = self._typeOptionMenu.getvalue()

        # Fetch the file (mapping empty string to None).
        file = self._fileEntryField.getvalue()
        if file == '':
            file = None

        # Get the contents of each active ParameterEditor.
        parameters = [parameterEditor.get() \
                      for parameterEditor in \
                      self._parameterEditors[:self._nActiveParameterEditors]]

        # Create the new Spectrum.
        spectrum = Spectrum(type, file, parameters)

        # Return the new Spectrum.
        return spectrum

    def set(self, spectrum):
        """Set the editor state.

        Parameters:

        self: This object.

        spectrum: (Spectrum): Object to set in this editor.

        Return value:

        None.

        Description:
        
        Set the fields using a Spectrum.
        """

        # Set the type OptionMenu.
        type = spectrum.getType()
        self._typeOptionMenu.setvalue(type)

        # Set the file field (mapping None to empty string).
        file = spectrum.getFile()
        if file is None:
            file = ''
        self._fileEntryField.setvalue(file)
        if type == 'FileFunction':
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
        parameters = spectrum.getParameters()
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

        Activate all of the child widgets in this SpectrumEditor.
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
        
        Deactivate all of the child widgets in this SpectrumEditor.
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

        type: (string) New Spectrum type string.

        Return value:

        None.

        Description:
        
        Process the selection of a new Spectrum type in the type
        OptionMenu. If a new Spectrum type is selected, clear the
        current Spectrum and create a default Spectrum of the new
        type.
        """

        # If the new type is the same as the previous type, no change
        # is needed.
        if type == self._referenceElement.getType():
            return

        # A new Spectrum type has been selected, so create a new one.
        spectrum = Spectrum(type = type)

        # Set the editor with the new Spectrum.
        self.set(spectrum)
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
    root.title('SpectrumEditor test')

    # Create and grid an editor for a default Spectrum, a button to
    # commit changes, and a button to dump its contents.
    spectrumEditor = SpectrumEditor()
    spectrumEditor.grid(row = 0, column = 0)
    commitButton = Tkinter.Button(root, text = 'Commit',
                                  command = spectrumEditor.commit)
    commitButton.grid(row = 0, column = 1)
    resetButton = Tkinter.Button(root, text = 'Reset',
                                  command = spectrumEditor.reset)
    resetButton.grid(row = 0, column = 2)
    printButton = Tkinter.Button(root, text = 'Print',
                                 command = \
                                 lambda: _print(spectrumEditor))
    printButton.grid(row = 0, column = 3)
    printXMLButton = Tkinter.Button(root, text = 'Print XML',
                                    command = \
                                    lambda: _printXML(spectrumEditor))
    printXMLButton.grid(row = 0, column = 4)

    # Enter the main program loop.
    root.mainloop()
