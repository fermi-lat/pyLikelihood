# $Id: SourceLibraryEditor.py,v 1.1.1.1.6.2 2014/04/29 19:24:46 tstephen Exp $

#******************************************************************************

# Import external modules.

# Standard modules
import Tkinter

# Third-party modules
import Pmw

# Project modules
from ElementEditor import ElementEditor
from Source import Source
from SourceLibrary import SourceLibrary
from SourceEditor import SourceEditor

#******************************************************************************

class SourceLibraryEditor(ElementEditor):
    """Class to edit ModelEditor SourceLibrary objects.

    Python implementation of the SourceLibraryEditor class which
    allows the user to edit the fields of a <source_library>
    element. This compound widget is designed to be embedded in other
    widgets.

    Attributes:

    _titleEntryField: (Pmw.EntryField) Controls editing of the
    SourceLibrary title.

    _sourceScrolledListBox: (Pmw.ScrolledListBox) For holding the list
    of Sources in the current SourceLibrary.
    
    _sourceEditor: (SourceEditor) For editing the current Source.
    """

    #--------------------------------------------------------------------------

    def __init__(self,
                 parent        = None,
                 sourceLibrary = None,
                 *args, **kwargs):
        """Initialize this object.

        Parameters:

        self: This object.
        
        parent: (Tkinter.Frame) Parent object for this widget.

        sourceLibrary: (SourceLibrary) SourceLibrary object to
        initialize fields.
        """

        # Initialize the parent class (which calls _makeWidgets and
        # set for this class).
        if sourceLibrary is None:
            sourceLibrary = SourceLibrary()
        ElementEditor.__init__(self, parent, sourceLibrary, *args, **kwargs)

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

        # Create and grid an EntryField for the SourceLibrary title.
        entryField = Pmw.EntryField(self,
                                    label_text = 'Title',
                                    modifiedcommand = (lambda: self._changeTitle(self._titleEntryField)),
                                    labelpos = 'w')
        entryField.grid(row = 0, column = 0, columnspan = 2)
        self._titleEntryField = entryField
        self._balloon.bind(self._titleEntryField,
                           'Enter the title of the source library.')

        # Create and grid a ScrolledListBox for the Source list.
        scrolledListBox = \
            Pmw.ScrolledListBox(self,
                                selectioncommand = self._onSelectSource)
        scrolledListBox.grid(row = 1, column = 0, sticky = 'ns')
        self._sourceScrolledListBox = scrolledListBox
        self._balloon.bind(self._sourceScrolledListBox,
                           'Select the source to edit.')

        # Create and grid a SourceEditor.
        sourceEditor = SourceEditor(self, borderwidth = 2, relief = 'ridge')
        sourceEditor.grid(row = 1, column = 1)
        self._sourceEditor = sourceEditor

    #--------------------------------------------------------------------------

    def get(self):
        """Return the contents of the editor.

        Parameters:

        self: This object.

        Return value:

        Copy of SourceLibrary being edited.

        Description:

        Return a new SourceLibrary containing the current state of the
        editor.
        """

        # Fetch the title EntryField value.
        title = self._titleEntryField.getvalue()

        # Save the current Source from the SourceEditor.
        source = self._sourceEditor.get()
        self._sources[self.getCurrentSourceIndex()] = source

        # Create a new SourceLibrary with the current values.
        sourceLibrary = SourceLibrary(title, self._sources)

        # Return the new SourceLibrary.
        return sourceLibrary

    def getSourceLibrary(self):
        """Return the existing Sources

        Parameters:

        self: This object.

        Return value:

        Copy of SourceLibrary being edited.

        Description:

        Return a new SourceLibrary containing the current list of sources.
        This new library does not contain changes (if any) made to the
        currently selected source that have not been saved
        """

        # Fetch the title EntryField value.
#        title = self._titleEntryField.getvalue()
        title = self._libraryTitle

        # Create a new SourceLibrary with the current values.
        sourceLibrary = SourceLibrary(title, self._sources)

        # Return the new SourceLibrary.
        return sourceLibrary

    def set(self, sourceLibrary):
        """Set the editor state.

        Parameters:

        self: This object.

        sourceLibrary: (SourceLibrary): Object to set in this editor.

        Return value:

        None.

        Description:
        
        Set the fields using a SourceLibrary.
        """

        # Fill in the title EntryField.
        title = sourceLibrary.getTitle()
        self._titleEntryField.setvalue(title)

        # Fetch the list of Sources.
        self._sources = sourceLibrary.getSources()

        # Fill in the Source list box with the Source names.
        items = [str(source.getName()) for source in self._sources]
        self._sourceScrolledListBox.setlist(items)

        # Select the first Source.
        self._sourceScrolledListBox.setvalue(items[0])
        self._currentSourceIndex = 0

        # Fill in the SourceEditor with the first Source.
        self._sourceEditor.set(self._sources[0])

    #--------------------------------------------------------------------------

    def enable(self):
        """Activate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:

        Activate all of the child widgets in this SourceLibraryEditor.
        """
        self._titleEntryField.configure(entry_state = 'normal')
        self._sourceScrolledListBox.configure(state = 'normal')
        self._sourceEditor.enable()

    def disable(self):
        """Deactivate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:
        
        Deactivate all of the child widgets in this SourceLibraryEditor.
        """
        self._titleEntryField.configure(entry_state = 'disabled')
        self._sourceScrolledListBox.configure(state = 'disabled')
        self._sourceEditor.enable()

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
        return self._currentSourceIndex

    #--------------------------------------------------------------------------

    def _onSelectSource(self):
        """Process a new Source selection.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:
        
        Respond to a click on a Source in the Source ScrolledListBox.
        """

        # Save the current Source from the SourceEditor.
        source = self._sourceEditor.get()
        self._sources[self.getCurrentSourceIndex()] = source

        # Fetch the index of the selected Source.
        selectedIndex = int(self._sourceScrolledListBox.component('listbox').\
                            curselection()[0])

        # Repopulate the ScrolledListBox to reflect any Source name
        # changes.
        items = [source.getName() for source in self._sources]
        self._sourceScrolledListBox.setlist(items)
        self._sourceScrolledListBox.setvalue(items[selectedIndex])

        # Assign the newly-selected Source to the SourceEditor.
        source = self._sources[selectedIndex]
        self._sourceEditor.set(self._sources[selectedIndex])
        self._currentSourceIndex = selectedIndex
        
        if(None != self._ds9Connector):
            self._ds9Connector.plotSources()

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

        # Select the specified source.
        self._sourceScrolledListBox.setvalue(sourceName)
        self._onSelectSource()

    #--------------------------------------------------------------------------

    def setDS9Connector(self,connector):
        self._ds9Connector = connector
        #we also need to pass it down to the source editor
        self._sourceEditor.setDS9Connector(connector)
        

    #--------------------------------------------------------------------------

    def _changeTitle(self,entryField):
        if (None != entryField):
            self._libraryTitle = entryField.getvalue()
        
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
    root.title('SourceLibraryEditor test')

    # Create a 2-source editor and a button to dump its contents.
    source1 = Source(name = 'Source 1')
    source2 = Source(name = 'Source 2')

    # Create the source library.
    sourceLibrary = SourceLibrary(title = '2 sources',
                                  sources = [source1, source2])

    # Create and grid the editor, a button to commit changes, and a
    # button to dump its contents.
    sourceLibraryEditor = SourceLibraryEditor(root, sourceLibrary)
    sourceLibraryEditor.grid(row = 0, column = 0)
    commitButton = Tkinter.Button(root, text = 'Commit',
                                  command = sourceLibraryEditor.commit)
    commitButton.grid(row = 0, column = 1)
    resetButton = Tkinter.Button(root, text = 'Reset',
                                  command = sourceLibraryEditor.reset)
    resetButton.grid(row = 0, column = 2)
    printButton = Tkinter.Button(root, text = 'Print',
                                 command = \
                                 lambda: _print(sourceLibraryEditor))
    printButton.grid(row = 0, column = 3)
    printXMLButton = Tkinter.Button(root, text = 'Print XML',
                                    command = \
                                    lambda: _printXML(sourceLibraryEditor))
    printXMLButton.grid(row = 0, column = 4)

    # Enter the main program loop.
    root.mainloop()
