# $Id: Element.py,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

#******************************************************************************

# Import external modules.

# Standard modules.
import types
import xml.dom.minidom

# Third-party modules.

# Project modules.

#******************************************************************************

class Element:
    """Generic Element class for ModelEditor.

    Description:

    This is a generic Element class to represent XML elements in
    ModelEditor files. This class also defines some XML-related
    utilities for use by its subclasses. This is an abstract base
    class, and should not be instantiated directly. All ModelEditor
    element classes should inherit from this class.

    Data attributes:

    _tagName: (string) XML element tag name for this Element.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Default tag name for this element.
    _defaultTagName = 'element'

    #--------------------------------------------------------------------------

    def __init__(self,
                 tagName = _defaultTagName,
                 dom     = None):
        """Initialize this Element.

        Parameters:

        self: This object.

        tagName (string): Tag name for this element.

        dom (xml.dom.minidom.Element): DOM element to convert to this
        Element. If this parameter is specified, the other parameters
        are ignored.

        Return value:

        None.

        Description:

        Initialize this Element. Currently, all this does is set the
        _tagName data attribute.

        Subclasses should call this method at the start of their own
        __init__() method.
        """

        # Set attributes.
        if dom:
            if isinstance(dom, xml.dom.minidom.Element):
                self.fromDom(dom)
            else:
                raise TypeError, 'Not a DOM element (%s)!' % dom
        else:
            self.setTagName(tagName)

    #--------------------------------------------------------------------------

    def __str__(self):
        """Return a string version of this Element.

        Parameters:

        self: This object.

        Return value:

        String representation of this Element.

        Description:

        Compute and return a string representation of this Element.
        This is done by using the internal __dict__ attribute to get
        the names and values of all data attributes. This method is
        used whenever the Element is evaluated in a string context,
        e.g. in a print statement. This method should work fine for
        all Element subclasses.
        """

        # Assemble a "key=value"-type format string for the data
        # attributes. Note that dictionary lookups will be used for
        # value substitution.
        names = self.__dict__.keys()
        names.sort()
        attributesFormat = ','.join(['%s=%%(%s)s' % (name, name)
                                     for name in names])

        # Assemble the complete format string.
        template = '%s(%s)' % (self.__class__.__name__, attributesFormat)

        # Compute string values for each data attribute, and save them
        # in a dictionary by attribute name.
        members = {}
        for k, v in self.__dict__.iteritems():
            if isinstance(v, types.ListType):
                members[k] = '[' + ','.join(str(x) for x in v) + ']'
            else:
                members[k] = str(v)

        # Populate the format string with the data attribute strings.
        s = template % members
    
        # Return the string.
        return s
        
    #--------------------------------------------------------------------------

    def __eq__(self, other = None):
        """Compare this and another Element for equality.

        Parameters:

        self: This object.

        other (Element): Element to compare against for equality.

        Return value:

        True if equal, False otherwise.

        Description:

        Compare the current Element to another Element for equality.
        Used by the '==' operator. The equality check is relatively
        expensive - it converts both objects to strings and compares
        the strings. This was done for simplicity. A more efficient
        method may be implemented later if needed. This method should
        work fine for Element subclasses.
        """

        # Return True if the objects are the same object.
        if self is other:
            return True

        # Return False if the string representations are not equal.
        if str(self) != str(other):
            return False

        # The objects are equal.
        return True

    def __ne__(self, other = None):
        """Compare this and another Element for inequality.

        Parameters:

        self: This object.

        other (Element): Element to compare against for inequality.

        Return value:

        True if unequal, False otherwise.

        Description:

        Compare the current Element to another Element for inequality.
        Used by the '!=' operator. The inequality check is relatively
        expensive - it converts both objects to strings and compares
        the strings. This was done for simplicity. A more efficient
        method may be implemented later if needed. This method should
        work fine for Element subclasses.
        """

        # Return False if the objects are the same object.
        if self is other:
            return False

        # Return True if the string representations are not equal.
        if str(self) != str(other):
            return True

        # The objects are equal.
        return False

    #--------------------------------------------------------------------------

    def toDom(self, domDocument = None):
        """Convert this Element to a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this Element.

        Return value:

        xml.dom.minidom.Element for this Element.

        Description:

        Convert this Element to an equivalent xml.dom.minidom.Element
        in the specified DOM document. For now, all this means is that
        a new xml.dom.minidom.Element object with the correct tag name
        is created, in the specified xml.dom.minidom.Document.

        Subclasses should call this method at the start of their own
        toDom() method, and then make any changes needed (usually
        adding attribute and child element nodes).
        """

        # Create the new DOM element with the appropriate tag name.
        dom = domDocument.createElement(self.getTagName())

        # Return the new DOM element.
        return dom

    def fromDom(self, dom = None):
        """Initialize this Element from a xml.dom.minodom.Element.

        Parameters:

        self: This object.

        dom (xml.dom.minidom.Element): DOM element to use when
        initializing this Element.

        Return value:

        None.

        Description:

        Use the specified DOM element as the source of the content of
        this Element. Currently, this method only sets the tag name of
        this Element.

        Subclasses should call this method at the start of their own
        fromDom() method, and then set the data attributes based on
        any other attribute or element nodes in the DOM element.
        """

        # Tag name
        self.setTagName(dom.tagName)

    #--------------------------------------------------------------------------

    def getTagName(self):
        """Return the tag name for this Element.

        Parameters:

        self: This object.

        Return value:

        String containing the tag name for this Element.

        Description:

        Return the tag name for this Element as a string.
        """
        return self._tagName

    def setTagName(self, tagName = None):
        """Set the tag name for this Element.

        Parameters:

        self: This object.

        tagName (string): New tag name for this Element.

        Return value:

        None.

        Description:

        Set the tag name for this Element to the specified string. If
        the new tag name is invalid, raise a TypeError exception.
        """
        if not self.validTagName(tagName):
            raise TypeError, 'Invalid tag name (%s)!' % tagName
        self._tagName = tagName

    def validTagName(self, tagName = None):
        """Check a tag name for validity.

        Parameters:

        self: This object.

        tagName (string): Proposed tag name for this Element.

        Return value:

        True if the tag name is valid, otherwise False.

        Description:

        Check if the proposed new tag name is valid. A tag name is
        valid if evaluates to a non-empty string.
        """
        if tagName is None:
            return False   # str(None) = 'None'
        try:
            tagName = str(tagName)
        except(TypeError):
            return False
        if tagName == '':
            return False
        return True

    #--------------------------------------------------------------------------

    def xmlBooleanToBoolean(self, boolean = None):
        """Convert a XML boolean value to a Python boolean value.

        Parameters:

        self: This object.

        boolean (string): XML boolean value ('true', '1', 'false', or
        '0').

        Return value:

        True if the XML boolean value represents truth, otherwise
        False.

        Description:

        Map a XML boolean value to a Python boolean value (True or
        False). XML boolean values are the strings 'true', 'false',
        '1', and '0'. If the value is not a valid XML boolean value,
        raise a TypeError exception.
        """
        if boolean == 'true' or boolean == '1':
            return True
        if boolean == 'false' or boolean == '0':
            return False
        raise TypeError, 'Invalid XML boolean value (%s)!' % boolean

    def booleanToXMLBoolean(self, boolean = None, numeric = False):
        """Convert a Python boolean value to a XML boolean value.

        Parameters:

        self: This object.

        boolean (bool): Python boolean value.

        numeric (bool): Set to True to return the XML boolean value as
        '1' or '0'. If not set, the XML boolean value will be returned
        as 'true' or 'false'.

        Return value:

        String. If numeric is False, return 'true' if bool is True,
        otherwise 'false'. If numeric is True, return '1' if bool is
        True, otherwise '0'.

        Description:

        Map a Python boolean value to a XML boolean value ('true',
        'false', '1', or '0'). If the value is not a valid Python
        boolean value, raise a TypeError exception.
        """
        if boolean == True:
            if numeric:
                return '1'
            else:
                return 'true'
        if boolean == False:
            if numeric:
                return '0'
            else:
                return 'false'
        raise TypeError, 'Invalid Python boolean value (%s)!' % boolean

#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.

if __name__ == '__main__':

    # Default constructor.
    element = Element()
    assert str(element) == 'Element(_tagName=element)'

    # Make the consructor fail.
    try:  # None for tag name
        element = Element(None)
        assert False
    except TypeError:
        pass
    try:  # Empty string for tag name.
        element = Element('')
        assert False
    except TypeError:
        pass
    try:  # None for tag name, by keyword.
        element = Element(tagName = None)
        assert False
    except TypeError:
        pass
    try:  # Empty string for tag name, by keyword.
        element = Element(tagName = '')
        assert False
    except TypeError:
        pass
    try:  # Pass a bad DOM element argument.
        element = Element(dom = Element())
        assert False
    except TypeError:
        pass

    # Set/get the tag name.
    element = Element()
    assert element.getTagName() == 'element'
    element.setTagName('anotherTest')
    assert element.getTagName() == 'anotherTest'
    try:  # Try to use None as the tag name.
        element.setTagName(None)
        assert False
    except TypeError:
        pass
    try:  # Try to use an empty string as the tag name.
        element.setTagName('')
        assert False
    except TypeError:
        pass

    # Constructor with attributes.
    element = Element('test')
    assert str(element) == 'Element(_tagName=test)'
    element = Element(tagName = 'test')
    assert str(element) == 'Element(_tagName=test)'

    # Convert to/from DOM object, and check the '==' and '!='
    # operators.
    domDocument = xml.dom.minidom.Document()
    dom = element.toDom(domDocument)
    elementCopy = Element(dom = dom)
    assert elementCopy == element
    assert not (elementCopy != element)
    assert element == element
    assert not (element != element)

    # Test the boolean conversion methods.
    assert element.xmlBooleanToBoolean('true') == True
    assert element.xmlBooleanToBoolean('1') == True
    assert element.xmlBooleanToBoolean('false') == False
    assert element.xmlBooleanToBoolean('0') == False
    assert element.booleanToXMLBoolean(True) == 'true'
    assert element.booleanToXMLBoolean(True, numeric = True) == '1'
    assert element.booleanToXMLBoolean(False) == 'false'
    assert element.booleanToXMLBoolean(False, numeric = True) == '0'
