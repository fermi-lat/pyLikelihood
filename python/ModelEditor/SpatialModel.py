# $Id: SpatialModel.py,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

#******************************************************************************

# Import external modules.

# Standard modules.
from copy import deepcopy
import xml.dom.minidom

# Third-party modules.

# Project modules.
from Element import Element
from Parameter import Parameter
from ParameterSet import ParameterSet

#******************************************************************************

class SpatialModel(Element, ParameterSet):
    """SpatialModel class to represent <spatialModel> elements in ModelEditor.

    Data attributes:

    _type: (string) Type string for the SpatialModel. Corresponds to
    the 'type' attribute of the <spatialModel> element.

    _file: (string) Path string for the SpatialModel. Corresponds to
    the optional 'file' attribute of the <spatialModel> element.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Define the tag name.
    _tagName = 'spatialModel'

    # Define the default parameters for each SpatialModel type.
    _defaultParameters = {
        'ConstantValue':
            [Parameter(name  = 'Value',
                       value = 1.0,
                       scale = 1.0,
                       min   = 0.0,
                       max   = 10.0,
                       free  = False)],
        'MapCubeFunction':
            [Parameter(name  = 'Normalization',
                       value = 1.0,
                       scale = 1.0,
                       min   = 0.001,
                       max   = 1000.0,
                       free  = False)],
        'SkyDirFunction':
            [Parameter(name  = 'RA',
                       value = 0.0,
                       scale = 1.0,
                       min   = 0.0,
                       max   = 360.0,
                       free  = False),
             Parameter(name  = 'DEC',
                       value = 0.0,
                       scale = 1.0,
                       min   = -90.0,
                       max   = 90.0,
                       free  = False)],
        'SpatialMap':
            [Parameter(name  = 'Prefactor',
                       value = 1.0,
                       scale = 1.0,
                       min   = 0.001,
                       max   = 1000.0,
                       free  = False)]
        }

    # Valid SpatialModel type strings.
    _validTypes = _defaultParameters.keys()

    # Define the default attributes.
    _defaultType = 'SkyDirFunction'
    _defaultFile = None
    _defaultConstructorParameters = None

    #--------------------------------------------------------------------------

    def __init__(self,
                 type       = _defaultType,
                 file       = _defaultFile,
                 parameters = _defaultConstructorParameters,
                 dom        = None,
                 *args, **kwargs):
        """Initialize this SpatialModel.

        Parameters:

        self: This object.

        type: (string) Type string for this SpatialModel.

        file: (string) Path to file containing SpatialModel data.

        parameters: (list of Parameter) One or more Parameters which
        define the SpatialModel.

        dom (xml.dom.minidom.Element): DOM element to convert to this
        SpatialModel. If this parameter is specified, the other
        parameters are ignored.

        Return value:

        None.

        Description:

        Initialize this SpatialModel. All data attributes are set from
        the corresponding parameters. If a DOM element is provided,
        use the attribute and element nodes of that DOM element to set
        the data attributes of this SpatialModel.
        """

        # Initialize the parent class. Do not pass the dom argument,
        # since it will be used if needed when fromDom() is called
        # below.
        Element.__init__(self, tagName = SpatialModel._tagName, *args,
                         **kwargs)

        # Set attributes.
        if dom:
            if isinstance(dom, xml.dom.minidom.Element):
                self.fromDom(dom)
            else:
                raise TypeError, 'Not a DOM element (%s)!' % dom
        else:
            self.setType(type)
            self.setFile(file)
            if parameters is None:
                parameters = SpatialModel._defaultParameters[type]
            self.setParameters(parameters)

    #--------------------------------------------------------------------------

    def toDom(self, domDocument):
        """Convert this SpatialModel to a xml.dom.minidom element.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this SpatialModel.

        Return value:

        xml.dom.minidom.Element for this SpatialModel.

        Description:

        Convert this SpatialModel to an equivalent
        xml.dom.minidom.Element in the specified DOM document. After
        the DOM element is created by the inherited toDom() method,
        the attribute and element nodes are set using the data
        attributes of this SpatialModel.
        """

        # Call the inherited method.
        dom = Element.toDom(self, domDocument)

        # type
        dom.setAttribute('type', self.getType())

        # file (skip if None)
        file = self.getFile()
        if file is not None:
            dom.setAttribute('file', file)

        # parameters
        for parameter in self.getParameters():
            domParameter = parameter.toDom(domDocument)
            dom.appendChild(domParameter)

        # Return the new DOM element.
        return dom

    def fromDom(self, dom):
        """Initialize this SpatialModel from a xml.dom.minidom element.

        Parameters:

        self: This object.

        dom (xml.dom.minidom.Element): DOM element to use when
        initializing this SpatialModel.

        Return value:

        None.

        Description:

        Use the specified DOM element as the source of the content of
        this SpatialModel. Set all data attributes using the
        corresponding attribute and element nodes of the DOM element.
        """

        # Call the inherited method.
        Element.fromDom(self, dom)

        # type
        self.setType(dom.getAttribute('type'))

        # file (map empty string to None)
        file = dom.getAttribute('file')
        if file == '':
            file = None
        self.setFile(file)

        # parameters
        self.setParameters([Parameter(dom = domParameter)
                            for domParameter
                            in dom.getElementsByTagName('parameter')])

    #--------------------------------------------------------------------------

    def getType(self):
        """Return the type for this SpatialModel.

        Parameters:

        self: This object.

        Return value:

        String containing the type for this SpatialModel.

        Description:

        Return the type for this SpatialModel as a string.
        """
        return self._type

    def setType(self, type):
        """Set the type for this SpatialModel.

        Parameters:

        self: This object.

        type (string): New type for this SpatialModel.

        Return value:

        None.

        Description:

        Set the type of this SpatialModel to the specified string. If
        an invalid type is specified, raise a TypeError exception.
        """
        if not self.validType(type):
            raise TypeError, 'Invalid SpatialModel type (%s)!' % type
        self._type = type

    def validType(self, type):
        """Check a type for validity.

        Parameters:

        self: This object.

        type (string): Proposed type for this SpatialModel.

        Return value:

        True if the type is valid, otherwise False.

        Description:

        Check if the proposed new type is valid. A type is valid if it
        is found in the list of valid type strings.
        """
        if type in self.getValidTypes():
            return True
        return False

    def getValidTypes(self):
        """Return the the list of valid SpatialModel types.

        Parameters:

        self: This object.

        Return value:

        List of strings containing the valid SpatialModel types.

        Description:

        Return the valid types for a SpatialModel as a list of
        strings.
        """
        return SpatialModel._validTypes

    #--------------------------------------------------------------------------

    def getFile(self):
        """Return the file for this SpatialModel.

        Parameters:

        self: This object.

        Return value:

        String containing the file for this SpatialModel.

        Description:

        Return the file for this SpatialModel as a string.
        """
        return self._file

    def setFile(self, file):
        """Set the file for this SpatialModel.

        Parameters:

        self: This object.

        file (string): New file for this SpatialModel.

        Return value:

        None.

        Description:

        Set the file of this SpatialModel to the specified string. If
        an invalid file is specified, raise a TypeError exception.
        """
        if not self.validFile(file):
            raise TypeError, 'Invalid SpatialModel file (%s)!' % file
        self._file = file

    def validFile(self, file):
        """Check a file for validity.

        Parameters:

        self: This object.

        file (string): Proposed file for this SpatialModel.

        Return value:

        True if the file is valid, otherwise False.

        Description:

        Check if the proposed new file is valid. A file is valid if it
        is None, or a non-empty string (make this more specific
        later).
        """
        if file is None:
            return True
        file = str(file)
        if file == '':
            return False
        return True

    #--------------------------------------------------------------------------

    def validParameters(self, parameters):
        """Check a parameter list for validity.

        Parameters:

        self: This object.

        parameters (list of Parameter): Proposed Parameters for this
        SpatialModel.

        Return value:

        True if the parameter list is valid, otherwise False.

        Description:

        Check if the proposed proposed parameter list is valid. A
        parameter list is valid if it contains a complete set of valid
        parameters for the SpatialModel type.
        """

        # Fetch the current SpatialModel type.
        type = self.getType()

        # Get the list of names of required parameters for this
        # SpatialModel type.
        requiredParameterNames = self.getRequiredParameterNames()

        # Get the list of names of the new parameters.
        parameterNames = [p.getName() for p in parameters]

        # Check if the sets are identical.
        if set(parameterNames) == set(requiredParameterNames):
            return True

        # The parameter list is invalid.
        return False

    def getRequiredParameterNames(self):
        """Return the list of names of required parameters for this SpatialModel.

        Parameters:

        self: This object.

        Return value:

        List of strings of required parameter names.

        Description:

        Return the list of names of parameters required by this
        SpatialModel. The list of required parametr names is
        determined by the SpatialModel type.
        """

        # Fetch the SpatialModel type.
        type = self.getType()
        names = [p.getName() for p in SpatialModel._defaultParameters[type]]
        return names

#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.

if __name__ == '__main__':

    # Default constructor
    spatialModel = SpatialModel()
    assert spatialModel == 'SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction)'

    # Constructor with attribute values.
    parameters = [Parameter('RA'),
                  Parameter('DEC')]
    spatialModel = SpatialModel(type = 'SkyDirFunction',
                                parameters = parameters)
    assert spatialModel == 'SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=None,_min=None,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=None,_min=None,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction)'

    # Check the parameter count method.
    assert spatialModel.getNumParameters() == 2

    # Check the Parameter access methods. 
    parameter = spatialModel.getParameterByIndex(0)
    assert str(parameter) == str(parameters[0])
    parameter = spatialModel.getParameterByName('DEC')
    assert str(parameter) == str(parameters[1])

    # Convert to/from DOM object.
    import xml.dom.minidom
    domDocument = xml.dom.minidom.Document()
    dom = spatialModel.toDom(domDocument)
    spatialModelCopy = SpatialModel(dom = dom)
    assert spatialModelCopy == spatialModel
