# $Id: Parameter.py,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

#******************************************************************************

# Import external modules.

# Standard modules.
import xml.dom.minidom

# Third-party modules.

# Project modules.
from Element import Element

#******************************************************************************

class Parameter(Element):
    """Parameter class to represent <parameter> elements in ModelEditor.

    Data attributes:

    _name: (string) Name of the Parameter. Corresponds to the 'name'
    attribute of the <parameter> element.

    _value: (float) Value of the Parameter. Corresponds to the 'value'
    attribute of the <parameter> element.

    _scale: (float) Scale factor for the Parameter value. Corresponds
    to the 'scale' attribute of the <parameter> element.

    _min: (float) Minimum valid value of the Parameter. If None, no
    minimum checking is performed. Corresponds to the 'min' attribute
    of the <parameter> element.

    _max: (float) Maximum valid value of the Parameter. If None, no
    maximum checking is performed. Corresponds to the 'max' attribute
    of the <parameter> element.

    _free: (Boolean) True if the Parameter value can be adjusted by
    the likelihood estimator, False otherwise. Corresponds to the
    'free' attribute of the <parameter> element.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Define the tag name.
    _tagName = 'parameter'

    # Define the attribute names and default values.
    _defaults = {
        'name' : 'parameter',
        'value': 0.0,
        'scale': 1.0,
        'min'  : None,
        'max'  : None,
        'free' : False
        }

    # The list of field names is used by the ParameterEditor to create
    # field labels. These strings must be explicitly listed since the
    # keys() method used on the _defaults dictionary returns the
    # strings in an unpredictable order.
    _fieldNames = ['name', 'value', 'scale', 'min', 'max', 'free']

    #--------------------------------------------------------------------------

    def __init__(self,
                 name  = _defaults['name'],
                 value = _defaults['value'],
                 scale = _defaults['scale'],
                 min   = _defaults['min'],
                 max   = _defaults['max'],
                 free  = _defaults['free'],
                 dom   = None,
                 *args, **kwargs):
        """Initialize this Parameter.

        Parameters:

        self: This object.

        name: (string) Name of the Parameter.

        value: (float) Value of the Parameter.

        scale: (float) Scale factor for the Parameter value.

        min: (float) Minimum valid value of the Parameter. If None, no
        minimum checking is performed.

        max: (float) Maximum valid value of the Parameter. If None, no
        maximum checking is performed.

        free: (Boolean) True if the Parameter value can be adjusted by
        the likelihood estimator, False otherwise.

        dom (xml.dom.minidom.Element): DOM element to convert to this
        Parameter. If this parameter is specified, the other
        parameters are ignored.

        Return value:

        None.

        Description:

        Initialize this Parameter. All data attributes are set from
        the corresponding parameters. If a DOM element is provided,
        use the attribute nodes of that DOM element to set the data
        attributes of this Parameter.
        """

        # Initialize the parent class. Do not pass the dom parameter,
        # since it will be used if needed when fromDom() is called
        # below.
        Element.__init__(self, Parameter._tagName, *args, **kwargs)

        # Set attributes.
        if dom:
            if isinstance(dom, xml.dom.minidom.Element):
                self.fromDom(dom)
            else:
                raise TypeError, 'Not a DOM element (%s)!' % dom
        else:
            self.setName(name)
            self.setMin(min)   # Set min, max before value to allow
            self.setMax(max)   # range checking when setValue() is called.
            self.setValue(value)
            self.setScale(scale)
            self.setFree(free)

   #--------------------------------------------------------------------------

    def toDom(self, domDocument = None):
        """Convert this Parameter to a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this Parameter.

        Return value:

        xml.dom.minidom.Element for this Parameter.

        Description:

        Convert this Parameter to an equivalent
        xml.dom.minidom.Element in the specified DOM document. After
        the DOM element is created by the inherited toDom() method,
        the attribute nodes are set using the data attributes of this
        Parameter.
        """

        # Call the inherited method.
        dom = Element.toDom(self, domDocument)

        # name
        dom.setAttribute('name', str(self.getName()))

        # value
        dom.setAttribute('value', str(self.getValue()))

        # scale
        dom.setAttribute('scale', str(self.getScale()))

        # min (skip if None)
        min = self.getMin()
        if min is not None:
            dom.setAttribute('min', str(min))

        # max (skip if None)
        max = self.getMax()
        if max is not None:
            dom.setAttribute('max', str(max))

        # free (map to XML boolean strings)
        free = self.getFree()
        free = self.booleanToXMLBoolean(free)
        dom.setAttribute('free', free)

        # Return the new DOM element.
        return dom

    def fromDom(self, dom):
        """Initialize this Parameter from a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        dom (xml.dom.minidom.Element): DOM element to use when
        initializing this Parameter.

        Return value:

        None.

        Description:

        Use the specified DOM element as the source of the content of
        this Parameter. Set all data attributes using the
        corresponding attribute nodes of the DOM element.
        """

        # Call the inherited method.
        Element.fromDom(self, dom)

        # name
        self.setName(dom.getAttribute('name'))

        # min (map empty string to None)
        min = dom.getAttribute('min')
        if min == '':
            min = None
        self.setMin(min)

        # max (map empty string to None)
        max = dom.getAttribute('max')
        if max == '':
            max = None
        self.setMax(max)

        # value (min and max set above to allow range checking).
        self.setValue(dom.getAttribute('value'))

        # scale
        self.setScale(dom.getAttribute('scale'))

        # free (map XML boolean string to True/False).
        free = dom.getAttribute('free')
        free = self.xmlBooleanToBoolean(free)
        self.setFree(free)

    #--------------------------------------------------------------------------

    def getName(self):
        """Return the name for this Parameter.

        Parameters:

        self: This object.

        Return value:

        String containing the name for this Parameter.

        Description:

        Return the name of this Parameter.
        """
        return self._name

    def setName(self, name):
        """Set the name for this Parameter.

        Parameters:

        self: This object.

        name (string): New name for this Parameter.

        Return value:

        None.

        Description:

        Set the name of this Parameter to the specified string. If the
        new name is invalid, raise a TypeError exception.
        """
        if not self.validName(name):
            raise TypeError, 'Invalid Parameter name (%s)!' % name
        self._name = str(name)

    def validName(self, name):
        """Check a Parameter name for validity.

        Parameters:

        self: This object.

        name (string): Proposed name for this Parameter.

        Return value:

        True if the name is valid, otherwise False.

        Description:

        Check if the proposed new name is valid. A name is valid if
        evaluates to a non-empty string.
        """
        if name is None:
            return False   # str(None) = 'None'
        try:
            name = str(name)
        except(TypeError):
            return False
        if name == '':
            return False
        return True

    #--------------------------------------------------------------------------

    def getValue(self):
        """Return the value for this Parameter.

        Parameters:

        self: This object.

        Return value:

        Float containing the value for this Parameter.

        Description:

        Return the value of this Parameter.
        """
        return self._value

    def setValue(self, value):
        """Set the value for this Parameter.

        Parameters:

        self: This object.

        value (float): New value for this Parameter.

        Return value:

        None.

        Description:

        Set the value of this Parameter to the specified value. If the
        new value is invalid, raise a TypeError exception.
        """
        if not self.validValue(value):
            raise TypeError, 'Invalid Parameter value (%s)!' % value
        self._value = float(value)

    def validValue(self, value):
        """Check a Parameter value for validity.

        Parameters:

        self: This object.

        value (float): Proposed value for this Parameter.

        Return value:

        True if the value is valid, otherwise False.

        Description:

        Return True if the value is valid, False otherwise. A value is
        valid if it evaluates to a float, and is within range of any
        existing limits.
        """
        try:
            value = float(value)
        except:
            return False
        min = self.getMin()
        if min is not None and value < min:
            return False
        max = self.getMax()
        if max is not None and value > max:
            return False
        return True

    #--------------------------------------------------------------------------

    def getScale(self):
        """Return the scale for this Parameter.

        Parameters:

        self: This object.

        Return value:

        Float containing the scale for this Parameter.

        Description:

        Return the scale of this Parameter.
        """
        return self._scale

    def setScale(self, scale):
        """Set the scale for this Parameter.

        Parameters:

        self: This object.

        scale (float): New scale for this Parameter.

        Return value:

        None.

        Description:

        Set the scale of this Parameter to the specified value. If the
        new scale is invalid, raise a TypeError exception.
        """
        if not self.validScale(scale):
            raise TypeError, 'Invalid Parameter scale (%s)!' % scale
        self._scale = float(scale)

    def validScale(self, scale):
        """Check a Parameter scale for validity.

        Parameters:

        self: This object.

        scale (float): Proposed scale for this Parameter.

        Return value:

        True if the value is valid, otherwise False.

        Description:

        Return True if the scale is valid, False otherwise. A scale is
        valid if it evaluates to a float.
        """
        try:
            scale = float(scale)
        except:
            return False
        return True

    #--------------------------------------------------------------------------

    def getMin(self):
        """Return the min for this Parameter.

        Parameters:

        self: This object.

        Return value:

        Float containing the min for this Parameter, or None if the
        min has not been set.

        Description:

        Return the min of this Parameter. If the min has not been set
        yet, return None.
        """
        if hasattr(self, '_min'):
            return self._min
        else:
            return None

    def setMin(self, min):
        """Set the min for this Parameter.

        Parameters:

        self: This object.

        min (float): New min for this Parameter.

        Return value:

        None.

        Description:

        Set the min of this Parameter to the specified value. If the
        new min is invalid, raise a TypeError exception.
        """
        if not self.validMin(min):
            raise TypeError, 'Invalid Parameter min (%s)!' % min
        if min is not None:
            min = float(min)
        self._min = min

    def validMin(self, min):
        """Check a Parameter min for validity.

        Parameters:

        self: This object.

        min (float): Proposed min for this Parameter.

        Return value:

        True if the min is valid, otherwise False.

        Description:

        Return True if the min is valid, False otherwise. A min is
        valid if it is None or evaluates to a float and is less than
        or equal to any existing max.
        """
        if min is None:
            return True
        try:
            min = float(min)
        except:
            return False
        max = self.getMax()
        if max is not None and min > max:
            return False
        return True

    #--------------------------------------------------------------------------

    def getMax(self):
        """Return the max for this Parameter.

        Parameters:

        self: This object.

        Return value:

        Float containing the max for this Parameter, or None if the
        max has not been set yet.

        Description:

        Return the max of this Parameter. If the max has not been set
        yet, return None.
        """
        if hasattr(self, '_max'):
            return self._max
        else:
            return None

    def setMax(self, max):
        """Set the max for this Parameter.

        Parameters:

        self: This object.

        max (float): New max for this Parameter.

        Return value:

        None.

        Description:

        Set the max of this Parameter to the specified value. If the
        new max is invalid, raise a TypeError exception.
        """
        if not self.validMax(max):
            raise TypeError, 'Invalid Parameter max (%s)!' % max
        if max is not None:
            max = float(max)
        self._max = max

    def validMax(self, max):
        """Check a Parameter max for validity.

        Parameters:

        self: This object.

        max (float): Proposed max for this Parameter.

        Return value:

        True if the max is valid, otherwise False.

        Description:

        Return True if the max is valid, False otherwise. A max is
        valid if it is None or evaluates to a float and is greater
        than or equal to any existing min.
        """
        if max is None:
            return True
        try:
            max = float(max)
        except:
            return False
        min = self.getMin()
        if min is not None and max < min:
            return False
        return True

    #--------------------------------------------------------------------------

    def getFree(self):
        """Return the free for this Parameter.

        Parameters:

        self: This object.

        Return value:

        Bool containing the free for this Parameter.

        Description:

        Return the free of this Parameter.
        """
        return self._free

    def setFree(self, free):
        """Set the free for this Parameter.

        Parameters:

        self: This object.

        free (bool): New free for this Parameter.

        Return value:

        None.

        Description:

        Set the free of this Parameter to the specified value. If the
        new free is invalid, raise a TypeError exception.
        """
        if not self.validFree(free):
            raise TypeError, 'Invalid Parameter free (%s)!' % free
        self._free = bool(free)

    def validFree(self, free):
        """Check a Parameter free for validity.

        Parameters:

        self: This object.

        free (bool): Proposed free for this Parameter.

        Return value:

        True if the free is valid, otherwise False.

        Description:

        Return True if the free is valid, False otherwise. A free is
        valid if it evaluates to True or False.
        """
        try:
            free = bool(free)
        except:
            return False
        return True

#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.

if __name__ == '__main__':

    # Default constructor.
    parameter = Parameter()
    assert str(parameter) == 'Parameter(_free=False,_max=None,_min=None,_name=parameter,_scale=1.0,_tagName=parameter,_value=0.0)'
    
    # Constructor with attribute values.
    parameter = Parameter(name = 'test', value = 1.0, scale = 2.0,
                          min = 0.0, max = 10.0, free = True)
    assert str(parameter) == 'Parameter(_free=True,_max=10.0,_min=0.0,_name=test,_scale=2.0,_tagName=parameter,_value=1.0)'

    # Convert to/from DOM object, and check the '==' and '!='
    # operators.
    domDocument = xml.dom.minidom.Document()
    dom = parameter.toDom(domDocument)
    parameterCopy = Parameter(dom = dom)
    assert parameterCopy == parameter
    assert not (parameterCopy != parameter)
