# $Id: Spectrum.py,v 1.4 2010/05/11 01:32:47 elwinter Exp $

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

class Spectrum(Element, ParameterSet):
    """Spectrum class to represent <spectrum> elements in ModelEditor.

    Data attributes:

    _type: (string) Type string for the Spectrum. Corresponds to the
    'type' attribute of the <spectrum> element.

    _file: (string) Path string for the Spectrum. Corresponds to the
    'file' attribute of the <spectrum> element.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Define the tag name.
    _tagName = 'spectrum'

    # Define the default parameters for each Spectrum type.
    _defaultParameters = {

        'PowerLaw':
        [
        Parameter(name  = 'Prefactor',
                  value = 1.0,
                  scale = 1.0e-9,
                  min   = 0.001,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = 'Index',
                  value = -2.1,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'Scale',
                  value = 100.0,
                  scale = 1.0,
                  min   = 30.0,
                  max   = 2000.0,
                  free  = False)
        ],

        'BrokenPowerLaw':
        [
        Parameter(name  = 'Prefactor',
                  value = 1.0,
                  scale = 1.0e-9,
                  min   = 0.001,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = 'Index1',
                  value = -1.8,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'BreakValue',
                  value = 1000.0,
                  scale = 1.0,
                  min   = 30.0,
                  max   = 2000.0,
                  free  = True),
        Parameter(name  = 'Index2',
                  value = -2.3,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True)
        ],

        'PowerLaw2':
        [
        Parameter(name  = 'Integral',
                  value = 1.0,
                  scale = 1.0e-6,
                  min   = 1.0e-5,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = 'Index',
                  value = -2.0,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'LowerLimit',
                  value = 20.0,
                  scale = 1.0,
                  min   = 20.0,
                  max   = 2.0e5,
                  free  = False),
        Parameter(name  = 'UpperLimit',
                  value = 2.0e5,
                  scale = 1.0,
                  min   = 20.0,
                  max   = 2.0e5,
                  free  = False)
        ],

        'BrokenPowerLaw2':
        [
        Parameter(name  = 'Integral',
                  value = 1.0,
                  scale = 1.0e-4,
                  min   = 0.001,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = 'Index1',
                  value = -1.8,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'Index2',
                  value = -2.3,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'BreakValue',
                  value = 1000.0,
                  scale = 1.0,
                  min   = 30.0,
                  max   = 1.0e4,
                  free  = True),
        Parameter(name  = 'LowerLimit',
                  value = 20.0,
                  scale = 1.0,
                  min   = 20.0,
                  max   = 2.0e5,
                  free  = False),
        Parameter(name  = 'UpperLimit',
                  value = 2.0e5,
                  scale = 1.0,
                  min   = 20.0,
                  max   = 2.0e5,
                  free  = False)
        ],

        'LogParabola':
        [
        Parameter(name  = 'norm',
                  value = 1.0,
                  scale = 1.0e-9,
                  min   = 0.001,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = 'alpha',
                  value = 1.0,
                  scale = 1.0,
                  min   = 0.0,
                  max   = 10.0,
                  free  = True),
        Parameter(name  = 'Eb',
                  value = 300.0,
                  scale = 1.0,
                  min   = 20.0,
                  max   = 1.0e4,
                  free  = True),
        Parameter(name  = 'beta',
                  value = 2.0,
                  scale = 1.0,
                  min   = 0.0,
                  max   = 10.0,
                  free  = True)
        ],

        'ExpCutoff':
        [
        Parameter(name  = 'Prefactor',
                  value = 50.0,
                  scale = 1.0e-9,
                  min   = 0.01,
                  max   = 1.0e5,
                  free  = True),
        Parameter(name  = 'Index',
                  value = -2.1,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'Scale',
                  value = 100.0,
                  scale = 1.0,
                  min   = 30.0,
                  max   = 2000.0,
                  free  = False),
        Parameter(name  = 'Ebreak',
                  value = 10.0,
                  scale = 1.0,
                  min   = 1.0,
                  max   = 300.0,
                  free  = True),
        Parameter(name  = 'P1',
                  value = 100.0,
                  scale = 1000.0,
                  min   = 0.1,
                  max   = 300.0,
                  free  = True),
        Parameter(name  = 'P2',
                  value = 0.0,
                  scale = 1.0,
                  min   = -1.0,
                  max   = 1.0,
                  free  = False),
        Parameter(name  = 'P3',
                  value = 0.0,
                  scale = 1.0,
                  min   = -1.0,
                  max   = 1.0,
                  free  = False)],

        "BrokenPowerLawExpCutoff":
        [
        Parameter(name  = 'Prefactor',
                  value = 1.0,
                  scale = 1.0e-9,
                  min   = 0.01,
                  max   = 1.0e5,
                  free  = True),
        Parameter(name  = 'Index1',
                  value = -2.1,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.001,
                  free  = True),
        Parameter(name  = 'Index2',
                  value = -2.1,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.001,
                  free  = True),
        Parameter(name  = 'BreakValue',
                  value = 1000.0,
                  scale = 1.0,
                  min   = 1.0,
                  max   = 1.0e4,
                  free  = True),
        Parameter(name  = 'Eabs',
                  value = 10.0,
                  scale = 1.0,
                  min   = 1.0,
                  max   = 300.0,
                  free  = True),
        Parameter(name  = 'P1',
                  value = 100.0,
                  scale = 1000.0,
                  min   = 0.1,
                  max   = 300.0,
                  free  = True)
        ],

        'Gaussian':
        [
        Parameter(name  = 'Prefactor',
                  value = 1.0,
                  scale = 1.0e-9,
                  min   = 0.001,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = 'Mean',
                  value = 7.0e4,
                  scale = 1.0,
                  min   = 1000.0,
                  max   = 1.0e5,
                  free  = True),
        Parameter(name  = 'Sigma',
                  value = 1000.0,
                  scale = 1.0,
                  min   = 30.0,
                  max   = 1.0e4,
                  free  = True)
        ],

        'ConstantValue':
        [
        Parameter(name  = 'Value',
                  value = 1.0,
                  scale = 1.0,
                  min   = 0.0,
                  max   = 10.0,
                  free  = False)
        ],

        'FileFunction':
        [
        Parameter(name  = 'Normalization',
                  value = 1.0,
                  scale = 1.0,
                  min   = 1.0e-5,
                  max   = 1.0e5,
                  free  = True)
        ],

        "BandFunction":
        [
        Parameter(name  = "norm",
                  value = 1.0,
                  scale = 1.0e-9,
                  min   = 1.0e-5,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = "alpha",
                  value = -1.8,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = "beta",
                  value = -2.5,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = "Ep",
                  value = 0.1,
                  scale = 1.0,
                  min   = 0.001,
                  max   = 10.0,
                  free  = True),
        Parameter(name  = "Scale",
                  value = 0.1,
                  scale = 1.0,
                  min   = 0.001,
                  max   = 1.0e5,
                  free  = False),
        ],

        'PLSuperExpCutoff':
        [
        Parameter(name  = 'Prefactor',
                  value = 1.0,
                  scale = 1.0e-7,
                  min   = 1.0e-5,
                  max   = 1000.0,
                  free  = True),
        Parameter(name  = 'Index1',
                  value = -1.7,
                  scale = 1.0,
                  min   = -5.0,
                  max   = 0.0,
                  free  = True),
        Parameter(name  = 'Scale',
                  value = 200.0,
                  scale = 1.0,
                  min   = 50.0,
                  max   = 1000.0,
                  free  = False),
        Parameter(name  = 'Cutoff',
                  value = 3000.0,
                  scale = 1.0,
                  min   = 500.0,
                  max   = 3.0e4,
                  free  = True),
        Parameter(name  = 'Index2',
                  value = 1.5,
                  scale = 1.0,
                  min   = 0.0,
                  max   = 5.0,
                  free  = True)
        ],

        'SmoothBrokenPowerLaw':
        [
        Parameter(name  = 'Prefactor',
                  value = 1.0,
                  scale = 1.0e-9,
                  min   = 0.0,
                  max   = 1.0e10,
                  free  = True),
        Parameter(name  = 'Index1',
                  value = -2.0,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'Scale',
                  value = 100.0,
                  scale = 1.0,
                  min   = 30.0,
                  max   = 2000.0,
                  free  = False),
        Parameter(name  = 'Index2',
                  value = -2.0,
                  scale = 1.0,
                  min   = -5.0,
                  max   = -1.0,
                  free  = True),
        Parameter(name  = 'BreakValue',
                  value = 1000.0,
                  scale = 1.0,
                  min   = 20.0,
                  max   = 5.0e5,
                  free  = True),
        Parameter(name  = 'Beta',
                  value = 0.2,
                  scale = 1.0,
                  min   = 0.01,
                  max   = 10.0,
                  free  = True)
        ],

        }

    # Valid Spectrum type strings.
    _validTypes = _defaultParameters.keys()

    # Define the default attributes.
    _defaultType = 'PowerLaw'
    _defaultFile = None
    _defaultConstructorParameters = None

    #--------------------------------------------------------------------------

    def __init__(self,
                 type       = _defaultType,
                 file       = _defaultFile,
                 parameters = _defaultConstructorParameters,
                 dom        = None,
                 *args, **kwargs):
        """Initialize this Spectrum.

        Parameters:

        self: This object.

        type: (string) Type string for this Spectrum.

        file: (string) Path to file containing Spectrum data.

        parameters: (list of Parameter) One or more Parameters which
        define the Spectrum.

        dom (xml.dom.minidom.Element): DOM element to convert to this
        Spectrum. If this parameter is specified, the other parameters
        are ignored.

        Return value:

        None.

        Description:

        Initialize this Spectrum. All data attributes are set from the
        corresponding parameters. If a DOM element is provided, use
        the attribute and element nodes of that DOM element to set the
        data attributes of this Spectrum.
        """

        # Initialize the parent class. Do not pass the dom argument,
        # since it will be used if needed when fromDom() is called
        # below.
        Element.__init__(self, Spectrum._tagName, *args, **kwargs)

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
                parameters = Spectrum._defaultParameters[type]
            self.setParameters(parameters)

    #--------------------------------------------------------------------------

    def toDom(self, domDocument):
        """Convert this Spectrum to a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this Spectrum.

        Return value:

        xml.dom.minidom.Element for this Spectrum.

        Description:

        Convert this Spectrum to an equivalent xml.dom.minidom.Element
        in the specified DOM document. After the DOM element is
        created by the inherited toDom() method, the attribute and
        element nodes are set using the data attributes of this
        Spectrum.
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
        """Initialize this Spectrum from a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        dom (xml.dom.minidom.Element): DOM element to use when
        initializing this Spectrum.

        Return value:

        None.

        Description:

        Use the specified DOM element as the source of the content of
        this Spectrum. Set all data attributes using the corresponding
        attribute and element nodes of the DOM element.
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
        """Return the type for this Spectrum.

        Parameters:

        self: This object.

        Return value:

        String containing the type for this Spectrum.

        Description:

        Return the type for this Spectrum as a string.
        """
        return self._type

    def setType(self, type):
        """Set the type for this Spectrum.

        Parameters:

        self: This object.

        type (string): New type for this Spectrum.

        Return value:

        None.

        Description:

        Set the type of this Spectrum to the specified string. If an
        invalid type is specified, raise a TypeError exception.
        """
        if not self.validType(type):
            raise TypeError, 'Invalid Spectrum type (%s)!' % type
        self._type = type

    def validType(self, type):
        """Check a type for validity.

        Parameters:

        self: This object.

        type (string): Proposed type for this Spectrum.

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
        """Return the the list of valid Spectrum types.

        Parameters:

        self: This object.

        Return value:

        List of strings containing the valid Spectrum types.

        Description:

        Return the valid types for a Spectrum as a list of strings.
        """
        return Spectrum._validTypes

    #--------------------------------------------------------------------------

    def getFile(self):
        """Return the file for this Spectrum.

        Parameters:

        self: This object.

        Return value:

        String containing the file for this Spectrum.

        Description:

        Return the file for this Spectrum as a string.
        """
        return self._file

    def setFile(self, file):
        """Set the file for this Spectrum.

        Parameters:

        self: This object.

        file (string): New file for this Spectrum.

        Return value:

        None.

        Description:

        Set the file of this Spectrum to the specified string. If an
        invalid file is specified, raise a TypeError exception.
        """
        if not self.validFile(file):
            raise TypeError, 'Invalid Spectrum file (%s)!' % file
        self._file = file

    def validFile(self, file):
        """Check a file for validity.

        Parameters:

        self: This object.

        file (string): Proposed file for this Spectrum.

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
        Spectrum.

        Return value:

        True if the parameter list is valid, otherwise False.

        Description:

        Check if the proposed parameter list is valid. A parameter
        list is valid if it contains a complete set of valid
        parameters for the spectrum type.
        """

        # Fetch the current Spectrum type.
        type = self.getType()

        # Get the list of names of required parameters for this
        # Spectrum type.
        requiredParameterNames = self.getRequiredParameterNames()

        # Get the list of names of the new parameters.
        parameterNames = [p.getName() for p in parameters]

        # Check if the sets are identical.
        if set(parameterNames) == set(requiredParameterNames):
            return True

        # The parameter list is invalid.
        return False

    def getRequiredParameterNames(self):
        """Return the list of names of required parameters for this Spectrum.

        Parameters:

        self: This object.

        Return value:

        List of strings of required parameter names.

        Description:

        Return the list of names of parameters required by this
        Spectrum. The list of required parametr names is determined by
        the Spectrum type.
         """

        # Fetch the Spectrum type.
        type = self.getType()
        names = [p.getName() for p in Spectrum._defaultParameters[type]]
        return names

#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.

if __name__ == '__main__':

    # Default constructor
    spectrum = Spectrum()
    assert spectrum == 'Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw)'

    # Constructor with attribute values.
    parameters = [Parameter('Prefactor'),
                  Parameter('Index'),
                  Parameter('Scale')]
    spectrum = Spectrum(type = 'PowerLaw', parameters = parameters)
    assert spectrum == 'Spectrum(_file=None,_parameters=[Parameter(_free=False,_max=None,_min=None,_name=Prefactor,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=None,_min=None,_name=Index,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=None,_min=None,_name=Scale,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spectrum,_type=PowerLaw)'

    # Check the parameter count method.
    assert spectrum.getNumParameters() == 3

    # Check the Parameter access methods. 
    parameter = spectrum.getParameterByIndex(0)
    assert str(parameter) == str(parameters[0])
    parameter = spectrum.getParameterByName('Scale')
    assert str(parameter) == str(parameters[2])

    # Convert to/from DOM object.
    import xml.dom.minidom
    domDocument = xml.dom.minidom.Document()
    dom = spectrum.toDom(domDocument)
    spectrumCopy = Spectrum(dom = dom)
    assert spectrumCopy == spectrum
