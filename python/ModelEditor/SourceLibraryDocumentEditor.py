# $Id: SourceLibraryDocumentEditor.py,v 1.1.1.1.6.4 2014/04/30 16:10:26 tstephen Exp $

#******************************************************************************

# Import external modules.

# Standard modules
import Tkinter

# Third-party modules
import Pmw

# Project modules
from SourceLibraryDocument import SourceLibraryDocument
from SourceLibraryEditor import SourceLibraryEditor

#******************************************************************************

class SourceLibraryDocumentEditor(Tkinter.Frame):
    """Class to edit ModelEditor SourceLibraryDocument objects.

    Python implementation of the SourceLibraryDocumentEditor class
    which allows the user to edit the contents of a XML document which
    conforms to the source_library.xsd schema. This compound widget is
    designed to be embedded in other widgets.

    Attributes:

    _sourceLibraryEditor: (SourceLibraryEditor) For editing the
    current <source_library> element.

    _referenceObject: (SourceLibraryDocument) Reference copy of the
    SourceLibraryDocument object being edited. Used to detect
    edits. This Element will be of whatever class the derived Editor
    class is designed to edit.

    """

    #--------------------------------------------------------------------------

    def __init__(self,
                 parent = None,
                 sourceLibraryDocument = None,
                 *args, **kwargs):
        """Initialize this object.

        Parameters:

        self: This object.

        parent: (Tkinter.Frame) Parent object for this widget.

        sourceLibraryDocument: (SourceLibraryDocument) Object to edit.
        """

        # Initialize the parent class. Note that this class does NOT
        # derive from ElementEditor.
        Tkinter.Frame.__init__(self, parent, *args, **kwargs)

        # Create widgets.
        self._makeWidgets()

        # Populate the editor.
        if sourceLibraryDocument is None:
            sourceLibraryDocument = SourceLibraryDocument()
        self.set(sourceLibraryDocument)
        self.commit()

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

        # Create and grid the editor for the <source_library> element.
        sourceLibraryEditor = SourceLibraryEditor(self, borderwidth = 2,
                                                  relief = 'ridge')
        sourceLibraryEditor.grid(row = 0, column = 0)
        self._sourceLibraryEditor = sourceLibraryEditor

    #--------------------------------------------------------------------------

    def get(self):
        """Return the contents of the editor.

        Parameters:

        self: This object.

        Return value:

        Copy of SourceLibraryDocument being edited.

        Description:

        Return a new SourceLibraryDocument containing the current
        state of the editor.
        """

        # Fetch the contents of the SourceLibrary editor.
        sourceLibrary = self._sourceLibraryEditor.get()

        # Create a new SourceLibraryDocument with the current values.
        sourceLibraryDocument = SourceLibraryDocument(sourceLibrary)

        # Return the new SourceLibraryDocument.
        return sourceLibraryDocument

    def getSourceLibrary(self):
        """Return the current list of sources.

        Parameters:

        self: This object.

        Return value:

        Copy of the current source list.

        Description:

        Return a new list of sources (as a raw SourceLibrary instead of 
        a Source Library Document) containing the current
        list of sources.  This new library  document does not 
        contain changes (if any) made to the
        currently selected source that have not been saved
        """

        # Fetch the contents of the SourceLibrary editor's source list.
        return self._sourceLibraryEditor.getSourceLibrary()


    def set(self, sourceLibraryDocument):
        """Set the editor state.

        Parameters:

        self: This object.

        sourceLibraryDocument: (SourceLibraryDocument): Object to set
        in this editor.

        Return value:

        None.

        Description:
        
        Set the fields using a SourceLibraryDocument.
        """

        # Fill in the SourceLibraryEditor.
        sourceLibrary = sourceLibraryDocument.getSourceLibrary()
        self._sourceLibraryEditor.set(sourceLibrary)

    #--------------------------------------------------------------------------

    def enable(self):
        """Activate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:

        Activate all of the child widgets in this
        SourceLibraryDocumentEditor.
        """
        self._sourceLibraryEditor.enable()

    def disable(self):
        """Deactivate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:
        
        Deactivate all of the child widgets in this
        SourceLibraryDocumentEditor.
        """
        self._sourceLibraryEditor.disable()

    def reset(self):
        """Reset this editor with the reference object.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:

        Replace the content of this editor with the reference object.
        """
        self.set(self._referenceObject)

    def commit(self):
        """Commit the current editor state to the reference object.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:

        Commit the current editor state to the reference object.
        """
        self._referenceObject = self.get()

    #--------------------------------------------------------------------------

    def getChanged(self):
        """Fetch the editor change status.

        Parameters:

        self: This object.

        Return value:

        True if the editor has changed, False otherwise.

        Description:
        
        Return False is the editor state matches the reference object,
        and True if not.
        """

        # Compute and return the current change status.
        changed = (self.get() != self._referenceObject)
        return changed

    #--------------------------------------------------------------------------

    def getCurrentSourceIndex(self):
        """Get the index of the currently selected Source.

        Parameters:

        self: This object.

        Return value:

        Integer containing the index of the Source selected in the
        Source selection list box.

        Description:
        
        Return the index of the currently selected Source.
        """
        return self._sourceLibraryEditor.getCurrentSourceIndex()

    #--------------------------------------------------------------------------

    def selectSource(self, sourceName):
        """Select a user-specified source.

        Parameters:

        self: This object.

        sourceName: (string) Name of source to select.

        Return value:

        None.

        Description:

        Manually select the designated Source in the source list box,
        and update the editor appropriately.
        """
#        print sourceName
        
        # Select the specified source.
        self._sourceLibraryEditor.selectSource(sourceName)

    #--------------------------------------------------------------------------

    def setDS9Connector(self,connector):
        self._ds9Connector = connector
        #the connector is really needed by the SourceLibraryEditor object so we pass it along
        self._sourceLibraryEditor.setDS9Connector(connector)
        
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
    document = editor.get()
    dom = document.toDom()
    print dom.toxml()
    if editor.getChanged():
        print "Changed by the editor."

if __name__ == '__main__':

    # Create the root window.
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title('SourceLibraryDocumentEditor test')

    # Create a 2-source library.
    from Source import Source
    source1 = Source(name = 'Source 1')
    source2 = Source(name = 'Source 2')

    # Create a SourceLibraryDocument from the 2 sources.
    from SourceLibrary import SourceLibrary
    sourceLibrary = SourceLibrary(title = '2 sources',
                                  sources = [source1, source2])
    sourceLibraryDocument = SourceLibraryDocument(sourceLibrary = \
                                                  sourceLibrary)

    # Create and grid the editor, a button to commit changes, and a
    # button to dump its contents.
    sourceLibraryDocumentEditor = \
        SourceLibraryDocumentEditor(root, sourceLibraryDocument)
    sourceLibraryDocumentEditor.grid(row = 0, column = 0)
    commitButton = Tkinter.Button(root, text = 'Commit',
                                  command = sourceLibraryDocumentEditor.commit)
    commitButton.grid(row = 0, column = 1)
    resetButton = Tkinter.Button(root, text = 'Reset',
                                  command = sourceLibraryDocumentEditor.reset)
    resetButton.grid(row = 0, column = 2)
    printButton = Tkinter.Button(root, text = 'Print',
                                 command = \
                                 lambda: _print(sourceLibraryDocumentEditor))
    printButton.grid(row = 0, column = 3)
    printXMLButton = Tkinter.Button(root, text = 'Print XML',
                                    command = \
                                    lambda: _printXML(sourceLibraryDocumentEditor))
    printXMLButton.grid(row = 0, column = 4)

    # Enter the main program loop.
    root.mainloop()
