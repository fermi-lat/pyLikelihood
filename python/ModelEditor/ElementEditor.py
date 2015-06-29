# $Id: ElementEditor.py,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

#******************************************************************************

# Import external modules.

# Standard modules
import Tkinter

# Third-party modules
import Pmw

# Project modules
from Element import Element

#******************************************************************************

class ElementEditor(Tkinter.Frame):
    """Class to edit ModelEditor Element objects.

    Generic ElementEditor class which allows the user to edit a XML
    element in a ModelEditor file. This is an abstract base class, and
    should not be instantiated directly. Subclasses of this widget
    should be designed to be embedded in other widgets. This widget
    simply creates an empty Frame.

    Data attributes:

    _referenceElement: (Element) Reference copy of the Element object
    being edited. Used to detect edits. This Element will be of
    whatever class the derived Editor class is designed to edit.

    _balloon: (Pmw.Balloon) Balloon help object.

    _tagNameLabel: (Tkinter.Label) Holds the tag name for the Element.
    """

    #--------------------------------------------------------------------------

    def __init__(self,
                 parent  = None,
                 element = None,
                 *args, **kwargs):
        """Initialize this ElementEditor.

        Parameters:

        self: This object.

        parent: (Tkinter.Frame) Parent object for this widget.

        element: (Element) Element to initialize editor.

        Return value:

        None.

        Description:

        Initialize this ElementEditor. This requires calling the
        _makeWidgets(), set(), and commit() methods, which are
        typically overridden by subclasses.

        Subclasses should call this method at the start of their own
        __init__() method.
        """

        # Initialize the parent class.
        Tkinter.Frame.__init__(self, parent, *args, **kwargs)

        # Create widgets.
        self._makeWidgets()

        # Populate the editor.
        if element is None:
            element = Element()
        self.set(element)
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

        # Create a Balloon object for help text.
        self._balloon = Pmw.Balloon(self)

        # Create a Label for the element tag name, but do not display it.
        self._tagNameLabel = Tkinter.Label(self)

    #--------------------------------------------------------------------------

    def get(self):
        """Return the contents of the editor.

        Parameters:

        self: This object.

        Return value:

        Copy of Element being edited.

        Description:
        
        Return a new Element containing the current state of the
        editor.
        """

        # Get the tag name.
        tagName = self._tagNameLabel.cget('text')

        # Make a new Element.
        element = Element(tagName)

        # Return the new Element.
        return element

    def set(self, element):
        """Set the editor state.

        Parameters:

        self: This object.

        element: (Element): Object to set in this editor.

        Return value:

        None.

        Description:

        Use the specified Element to set the editor state.
        """

        # Set the tag name.
        tagName = element.getTagName()
        self._tagNameLabel.configure(text = tagName)

    def clear(self):
        """Clear this editor.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:

        Does nothing. Must be overridden by subclasses.
        """
        pass

    def reset(self):
        """Reset this editor with the reference Element.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:

        Replace the content of this editor with the reference
        element. This method should not require overriding by
        subclasses.
        """
        self.set(self._referenceElement)

    def commit(self):
        """Commit the current editor state to the reference object.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:

        Commit the current editor state to the reference object. This
        method should not require overriding by subclasses.
        """
        self._referenceElement = self.get()

    #--------------------------------------------------------------------------

    def enable(self):
        """Activate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:

        Activate all of the child widgets in this ElementEditor.
        """
        pass

    def disable(self):
        """Deactivate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:
        
        Deactivate all of the child widgets in this ElementEditor.
        """
        pass

    #--------------------------------------------------------------------------

    def getChanged(self):
        """Fetch the editor change status.

        Parameters:

        self: This object.

        Return value:

        True if the editor contents do not correspond to the reference
        element, False otherwise.

        Description:
        
        Return False is the editor state matches the reference object,
        and True if not.
        """

        # Compute and return the current change status.
        changed = (str(self.get()) != str(self._referenceElement))
        return changed

#******************************************************************************

# Self-test code.

if __name__ == '__main__':

    # Create the root window.
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title('ElementEditor test')

    # Create a defaut ElementEditor.
    elementEditor = ElementEditor(root)

    # Enter the main program loop.
    root.mainloop()
