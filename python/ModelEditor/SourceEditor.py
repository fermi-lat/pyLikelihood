# $Id: SourceEditor.py,v 1.1.1.1.6.1 2014/04/16 14:53:55 tstephen Exp $

#******************************************************************************

# Import external modules.

# Standard modules
import Tkinter

# Third-party modules
import Pmw

# Project modules
from ElementEditor import ElementEditor
from Source import Source
from SpectrumEditor import SpectrumEditor
from SpatialModelEditor import SpatialModelEditor

#******************************************************************************

class SourceEditor(ElementEditor):
    """Class to edit ModelEditor Source objects.

    Python implementation of the SourceEditor class which allows the
    user to edit the fields of a <source> element. This compound
    widget is designed to be embedded in other widgets.

    Attributes:

    _nameEntryField: (Pmw.EntryField) Controls editing of the Source
    name.

    _typeLabel: (Tkinter.Label) Displays the Source type. Note that
    this value cannot be changed by the user.

    _spectrumEditor: (SpectrumEditor) For editing the Spectrum.

    _spatialModelEditor: (SpatialModelEditor) For editing the
    SpatialModel.
    """

    #--------------------------------------------------------------------------

    def __init__(self,
                 parent = None,
                 source = None,
                 *args, **kwargs):
        """Initialize this object.

        Parameters:

        self: This object.
        
        parent: (Tkinter.Frame) Parent object for this widget.
 
        source: (Source) Source to initialize fields.

        Return value:

        None.

        Description:

        Initialize this SourceEditor.
        """

        # Initialize the parent class (which calls _makeWidgets and
        # set for this class).
        if source is None:
            source = Source()
        ElementEditor.__init__(self, parent, source, *args, **kwargs)

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

        # Create and grid an EntryField for the Source name.
        entryField = Pmw.EntryField(self, label_text = 'Source Name:',
                                    labelpos = 'w')
        entryField.grid(row = 0, column = 0, sticky = 'w')
        self._nameEntryField = entryField
        self._balloon.bind(self._nameEntryField, 'Enter the source name.')

        # Create and grid a Label for the Source type.
        label = Tkinter.Label(self, text = 'Source Type:')
        label.grid(row = 0, column = 1, sticky = 'e')
        self._typeLabel = label

        # Create and grid a SpectrumEditor.
        spectrumEditor = SpectrumEditor(self, borderwidth = 2,
                                        relief = 'ridge')
        spectrumEditor.grid(row = 1, column = 0, columnspan = 2, sticky = 'ew')
        self._spectrumEditor = spectrumEditor

        # Create and grid a SpatialModel editor.
        spatialModelEditor = SpatialModelEditor(self, borderwidth = 2,
                                                relief = 'ridge')
        spatialModelEditor.grid(row = 2, column = 0, columnspan = 2,
                                sticky = 'ew')
        self._spatialModelEditor = spatialModelEditor

    #--------------------------------------------------------------------------

    def get(self):
        """Return the contents of the editor.

        Parameters:

        self: This object.

        Return value:

        Copy of Source being edited.

        Description:

        Return a new Source containing the current state of the
        editor.
        """

        # Get the name EntryField value.
        name = self._nameEntryField.getvalue()

        # Fetch the type Label and strip out header text.
        type = self._typeLabel['text']
        type = type.replace('Source Type:', '')

        # Get the contents of the SpectrumEditor.
        spectrum = self._spectrumEditor.get()

        # Get the contents of the SpatialModelEditor.
        spatialModel = self._spatialModelEditor.get()

        # Make a new Source from the current field values.
        source = Source(name, type, spectrum, spatialModel)

        # Return the new Source.
        return source

    def set(self, source):
        """Set the editor state.

        Parameters:

        self: This object.

        source: (Source): Object to set in this editor.

        Return value:

        None.

        Description:
        
        Set the fields using a Source.
        """

        # Fill in the name EntryField.
        name = source.getName()
        self._nameEntryField.setvalue(name)

        # Fill in the type Label.
        type = source.getType()
        self._typeLabel.configure(text = 'Source Type:' + type)

        # Fill out the SpectrumEditor.
        spectrum = source.getSpectrum()
        self._spectrumEditor.set(spectrum)

        # Fill out the SpatialModel editor.
        spatialModel = source.getSpatialModel()
        self._spatialModelEditor.set(spatialModel)

    #--------------------------------------------------------------------------

    def enable(self):
        """Activate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:

        Activate all of the child widgets in this SourceEditor.
        """
        self._nameEntryField.configure(entry_state = 'normal')
        self._typeLabel.configure(state = 'normal')
        self._spectrumEditor.enable()
        self._spatialModelEditor.enable()

    def disable(self):
        """Deactivate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:
        
        Deactivate all of the child widgets in this SourceEditor.
        """
        self._nameEntryField.configure(entry_state = 'disabled')
        self._typeLabel.configure(state = 'disabled')
        self._spectrumEditor.disable()
        self._spatialModelEditor.disable()

    #--------------------------------------------------------------------------

    def setDS9Connector(self,connector):
        self._ds9Connector = connector
        #we and finally down to the SpatialModelEditor down to the source editor
        self._spatialModelEditor.setDS9Connector(connector)
        
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
    root.title('SourceEditor test')

    # Create and grid the editor, a button to commit changes, and a
    # button to dump its contents.
    sourceEditor = SourceEditor(root)
    sourceEditor.grid(row = 0, column = 0)
    commitButton = Tkinter.Button(root, text = 'Commit',
                                  command = sourceEditor.commit)
    commitButton.grid(row = 0, column = 1)
    resetButton = Tkinter.Button(root, text = 'Reset',
                                  command = sourceEditor.reset)
    resetButton.grid(row = 0, column = 2)
    printButton = Tkinter.Button(root, text = 'Print',
                                 command = \
                                 lambda: _print(sourceEditor))
    printButton.grid(row = 0, column = 3)
    printXMLButton = Tkinter.Button(root, text = 'Print XML',
                                    command = \
                                    lambda: _printXML(sourceEditor))
    printXMLButton.grid(row = 0, column = 4)

    # Enter the main program loop.
    root.mainloop()
