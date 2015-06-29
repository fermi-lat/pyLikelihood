# $Id: ParameterEditor.py,v 1.1.1.1.6.1 2014/04/16 14:53:55 tstephen Exp $

#******************************************************************************

# Import external modules.

# Standard modules
import Tkinter

# Third-party modules
import Pmw

# Project modules
from ElementEditor import ElementEditor
from Parameter import Parameter

#******************************************************************************

class ParameterEditor(ElementEditor):
    """Class to edit ModelEditor Parameter objects.

    ParameterEditor class which allows the user to edit the fields of
    a <parameter> element. This compound widget is designed to be
    embedded in other widgets.

    Data attributes:

    _nameEntryField: (Pmw.EntryField) For editing the Parameter
    name. Name may be any string.

    _valueEntryField: (Pmw.EntryField) For editing the Parameter
    value. Value must be a floating-point number.

    _scaleEntryField: (Pmw.EntryField) For editing the Parameter scale
    factor. Scale must be a floating-point number.

    _minEntryField: (Pmw.EntryField) For editing the minimum allowed
    Parameter value. If present, min must be a floating-point number.

    _maxEntryField: (Pmw.EntryField) For editing the maximum allowed
    Parameter value. If present, max must be a floating-point number.

    _freeCheckbutton: (Tkinter.Checkbutton) For setting the Parameter
    free flag.

    _free: (Tkinter.BooleanVar) Control variable for free flag
    checkbutton.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Define the text field width in characters.
    _minTextFieldWidth = 10
    _textFieldWidth = max([len(s) for s in Parameter._fieldNames])
    _textFieldWidth = max(_textFieldWidth, _minTextFieldWidth)

    # Flag to determine if field labels should be shown.
    _showLabels = False

    #--------------------------------------------------------------------------

    def __init__(self,
                 parent     = None,
                 parameter  = None,
                 showLabels = False,
                 *args, **kwargs):
        """Initialize this ParameterEditor.

        Parameters:

        self: This object.

        parent: (Tkinter.Frame) Parent object for this widget.

        parameter: (Parameter) Parameter to initialize fields.

        showLabels: (Boolean) True if labels should be printed above
        the fields, False otherwise.

        Return value:

        None.

        Description:

        Initialize this ParameterEditor.
        """
        self._ds9Connector = None
        # Set the label printing flag.
        ParameterEditor._showLabels = showLabels

        # Initialize the parent class (which calls _makeWidgets and
        # set for this class).
        if parameter is None:
            parameter = Parameter()
        ElementEditor.__init__(self, parent, parameter, *args, **kwargs)
        

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

        # Start at the top row.
        row = 0

        # If labels were requested, create and grid them above the
        # EntryFields.
        if ParameterEditor._showLabels:
            col = 0
            for fieldName in Parameter._fieldNames:
                label = Tkinter.Label(self, text = fieldName,
                                      width = ParameterEditor._textFieldWidth)
                label.grid(row = row, column = col, sticky = 'ew')
                col += 1
            row += 1

        # Create and grid an arbitrary string EntryField for the
        # Parameter name.
        entryField = Pmw.EntryField(self, entry_width = \
                                    ParameterEditor._textFieldWidth)
        entryField.grid(row = row, column = 0)
        self._nameEntryField = entryField
        self._balloon.bind(self._nameEntryField, 'Edit the parameter name.')

        # Create and grid a real-number EntryField for the Parameter
        # value.
        entryField = Pmw.EntryField(self, validate = 'real', entry_width = \
                                    ParameterEditor._textFieldWidth, \
                                    modifiedcommand = (lambda: self._updateDS9()) \
                                    )
        entryField.grid(row = row, column = 1)
        self._valueEntryField = entryField
        self._balloon.bind(self._valueEntryField, 'Edit the parameter value.')

        # Create and grid a real-number EntryField for the Parameter
        # scale.
        entryField = Pmw.EntryField(self, validate = 'real', entry_width = \
                                    ParameterEditor._textFieldWidth)
        entryField.grid(row = row, column = 2)
        self._scaleEntryField = entryField
        self._balloon.bind(self._scaleEntryField,
                           'Edit the scale factor for the parameter value.')

        # Create and grid a real-number EntryField for the Parameter
        # minimum value.
        entryField = Pmw.EntryField(self, validate = 'real', entry_width = \
                                    ParameterEditor._textFieldWidth,
                                    command = self._updateValidation)
        entryField.grid(row = row, column = 3)
        self._minEntryField = entryField
        self._balloon.bind(self._minEntryField,
                           'Edit the minimum value for the parameter value.')

        # Create and grid a real-number EntryField for the Parameter
        # maximum value.
        entryField = Pmw.EntryField(self, validate = 'real', entry_width = \
                                    ParameterEditor._textFieldWidth,
                                    command = self._updateValidation)
        entryField.grid(row = row, column = 4)
        self._maxEntryField = entryField
        self._balloon.bind(self._maxEntryField,
                           'Edit the maximum value for the parameter value.')

        # Create and grid a Checkbutton for the Parameter free
        # flag. Note that we also must create a BooleanVar to store
        # the state of the Checkbutton.
        self._free = Tkinter.BooleanVar()
        checkbutton = Tkinter.Checkbutton(self, variable = self._free,
                                          width = ParameterEditor.\
                                          _textFieldWidth)
        checkbutton.grid(row = row, column = 5)
        self._freeCheckbutton = checkbutton
        self._balloon.bind(self._freeCheckbutton,
                           'Check to allow parameter adjustment by the ' +
                           'likelihood estimator.')

    #--------------------------------------------------------------------------

    def get(self):
        """Return the contents of the editor.

        Parameters:

        self: This object.

        Return value:

        Copy of Parameter being edited.

        Description:
        
        Return a new Parameter containing the current state of the
        editor. Note that the inherited get method need not be called,
        since its work (setting the _tagName attribute of this object)
        will be done by the Parameter constructor call.
        """

        # Get the name EntryField value.
        name = self._nameEntryField.getvalue()

        # Get the value EntryField value.
        value = self._valueEntryField.getvalue()

        # Get the scale EntryField value.
        scale = self._scaleEntryField.getvalue()
        
        # Get the min EntryField value, mapping empty string to None.
        min = self._minEntryField.getvalue()
        if min == '': min = None

        # Get the max EntryField value, mapping empty string to None.
        max = self._maxEntryField.getvalue()
        if max == '': max = None

        # Get the status of the free Checkbutton.
        free = self._free.get()

        # Make a new Parameter from the current field values.
        parameter = Parameter(name, value, scale, min, max, free)

        # Return the new Parameter.
        return parameter

    def set(self, parameter):
        """Set the editor state.

        Parameters:

        self: This object.

        parameter: (Parameter): Object to set in this editor.

        Return value:

        None.

        Description:

        Set the fields using a Parameter. The inherited set method is
        not needed, since all it does is set the _tagNameLabel
        attribute, which should be fixed as 'parameter'.
        """
        self._disableDS9Update = True  # disable updates while loading external data

        # Fill in the name EntryField.
        name = parameter.getName()
        self._nameEntryField.setvalue(name)

        # Fill in the value EntryField.
        value = parameter.getValue()
        self._valueEntryField.setvalue(value)

        # Fill in the scale EntryField.
        scale = parameter.getScale()
        self._scaleEntryField.setvalue(scale)

        # Fill in the min EntryField, mapping None to empty string.
        min = parameter.getMin()
        if min is None:
            min = ''
        self._minEntryField.setvalue(min)

        # Fill in the max EntryField, mapping None to empty string.
        max = parameter.getMax()
        if max is None:
            max = ''
        self._maxEntryField.setvalue(max)

        # Set the state of the free checkbutton as needed.
        if parameter.getFree():
            self._freeCheckbutton.select()
        else:
            self._freeCheckbutton.deselect()

        # Update the validation for the value field.
        self._updateValidation()

        self._disableDS9Update = False  # re-enable once data is loaded

    def clear(self):
        """Clear this editor.

        Parameters:

        self: This object.

        Return value:

        None.

        Description:

        Clear all of the fields in this editor.
        """
        self._disableDS9Update = True  # disable ds9 updates while resetting data
        self._nameEntryField.setvalue('')
        self._valueEntryField.setvalue('')
        self._scaleEntryField.setvalue('')
        self._minEntryField.setvalue('')
        self._maxEntryField.setvalue('')
        self._freeCheckbutton.deselect()

        # Update the validation for the value field.
        self._updateValidation()
        self._disableDS9Update = False  #re-enable once done

    #--------------------------------------------------------------------------

    def enable(self):
        """Activate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:

        Activate all of the child widgets in this ParameterEditor.
        """
        self._nameEntryField.configure(entry_state = 'normal')
        self._valueEntryField.configure(entry_state = 'normal')
        self._scaleEntryField.configure(entry_state = 'normal')
        self._minEntryField.configure(entry_state = 'normal')
        self._maxEntryField.configure(entry_state = 'normal')
        self._freeCheckbutton.configure(state = 'normal')

    def disable(self):
        """Deactivate all child widgets.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:
        
        Deactivate all of the child widgets in this ParameterEditor.
        """
        self._nameEntryField.configure(entry_state = 'disabled')
        self._valueEntryField.configure(entry_state = 'disabled')
        self._scaleEntryField.configure(entry_state = 'disabled')
        self._minEntryField.configure(entry_state = 'disabled')
        self._maxEntryField.configure(entry_state = 'disabled')
        self._freeCheckbutton.configure(state = 'disabled')

    #--------------------------------------------------------------------------

    def _updateValidation(self):
        """Update validation options for value field.

        Parameters:

        self: This object.

        Return value:

        None:

        Description:

        This method updates the validation requirements for the value
        field by incorporating restrictions based on the current min
        and max fields.
        """
        min = self._minEntryField.getvalue()
        if min == '':
            min = None
        max = self._maxEntryField.getvalue()
        if max == '':
            max = None
        value = self._valueEntryField.getvalue()
        self._valueEntryField.configure(validate = {'validator': 'real',
                                                    'min': min, 'max': max})
        self._minEntryField.configure(validate = {'validator': 'real',
                                                  'max': max})
        self._maxEntryField.configure(validate = {'validator': 'real',
                                                  'min': min})
        
    #--------------------------------------------------------------------------

    def setDS9Connector(self,connector):
        self._ds9Connector = connector
        
    def _updateDS9(self):
        if (None != self._ds9Connector and not self._disableDS9Update):
            self._ds9Connector.plotSources()

#******************************************************************************

# Self-test code.
import xml.dom.minidom
domDocument = xml.dom.minidom.Document()

# Printing routine for buttons.
def _print(editor):
    print editor.get()
    if editor.getChanged(): print "Changed by the editor."

# XML printing routine for buttons.
def _printXML(editor):
    element = editor.get()
    dom = element.toDom(domDocument)
    print dom.toxml()
    if editor.getChanged(): print "Changed by the editor."

if __name__ == '__main__':

    # Create the root window.
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title('ParameterEditor test')

    # Create and grid a labeled editor, buttons to commit and reset
    # changes, and buttons to dump the current contents in string and
    # XML form.
    parameterEditor = ParameterEditor(root, showLabels = True)
    parameterEditor.grid(row = 0, column = 0)
    commitButton = Tkinter.Button(root, text = 'Commit',
                                  command = parameterEditor.commit)
    commitButton.grid(row = 0, column = 1)
    resetButton = Tkinter.Button(root, text = 'Reset',
                                  command = parameterEditor.reset)
    resetButton.grid(row = 0, column = 2)
    printButton = Tkinter.Button(root, text = 'Print',
                                 command = \
                                 lambda: _print(parameterEditor))
    printButton.grid(row = 0, column = 3)
    printXMLButton = Tkinter.Button(root, text = 'Print XML',
                                    command = \
                                    lambda: _printXML(parameterEditor))
    printXMLButton.grid(row = 0, column = 4)

    # Enter the main program loop.
    root.mainloop()
