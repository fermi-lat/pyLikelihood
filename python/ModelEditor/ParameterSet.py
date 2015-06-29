# $Id: ParameterSet.py,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

#******************************************************************************

# Import external modules.

# Standard modules.
from copy import deepcopy

# Third-party modules.

# Project modules.

#******************************************************************************

class ParameterSet():
    """Interface to represent sets of <parameter> elements in ModelEditor.

    Data attributes:

    _parameters: (list of Parameter) List of Parameters which define
    this set. Corresponds to the child <parameter> elements of the XML
    element for this set.
    """

    #--------------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        """Initialize this ParameterSet.

        Parameters:

        None.

        Return value:

        None.

        Description:

        Initialize this ParameterSet.
        """
        self._parameters = []

    #--------------------------------------------------------------------------

    def getParameters(self):
        """Return a copy of the parameters for this set.

        Parameters:

        None.

        Return value:

        List containing copies of the parameters for this set.

        Description:

        Return a list containing copies of the Parameters for this
        set.
        """
        return deepcopy(self._parameters)

    def setParameters(self, parameters = None):
        """Set the parameters for this set.

        Parameters:

        parameters (list of Parameter): Parameters for this set.

        Return value:

        None.

        Description:

        Set the parameters for this set to a copy of the specified
        list of Parameters. If the list is invalid, raise a TypeError
        exception.
        """
        if not self.validParameters(parameters):
            raise TypeError, 'Invalid parameter set (%s)!' % \
                  ','.join(str(p) for p in parameters)
        self._parameters = deepcopy(parameters)

    def validParameters(self, parameters):
        """Check a parameter list for validity.

        Parameters:

        parameters (list of Parameter): Proposed Parameters for this
        set.

        Return value:

        True if the parameter list is valid, otherwise False.

        Description:

        Check if the proposed proposed parameter list is valid.
        """
        return True

    def getNumParameters(self):
        """Return the number of parameters for this set.

        Parameters:

        Return value:

        Integer containing the number of parameters for this set.

        Description:

        Return the number of parameters in this set.
        """
        return len(self._parameters)

    #--------------------------------------------------------------------------

    def getParameterByIndex(self, parameterIndex):
        """Return a copy of the Parameter at the specified position.

        Parameters:

        parameterIndex: (integer) Index of Parameter to retrieve.

        Return value:

        Copy of Parameter at the specified position.

        Description:

        Return a copy of the Parameter at the specified position in
        the list of Parameters for this set.
        """
        parameter = deepcopy(self._parameters[parameterIndex])
        return parameter

    def setParameterByIndex(self, parameterIndex, parameter):
        """Set the Parameter at the specified position.

        Parameters:

        parameterIndex: (integer) Index of Parameter to set.

        parameter: (Parameter) New Parameter to use.

        Return value:

        None.

        Description:

        Set the Parameter at the specified position in the list of
        Parameters for this set.
        """
        self._parameters[parameterIndex] = deepcopy(parameter)

    #--------------------------------------------------------------------------

    def getParameterByName(self, parameterName):
        """Get the Parameter with the specified name.

        Parameters:

        parameterName: (string) Name of Parameter to retrieve.

        Return value:

        Copy of Parameter with the specified name.

        Description:

        Return a copy of the Parameter with the specified name. Note
        that if more than one Parameter has the same name, a copy of
        the first Parameter with the specified name is returned.
        """
        parameterIndex = self.parameterNameToIndex(parameterName)
        parameter = self.getParameterByIndex(parameterIndex)
        return parameter

    def setParameterByName(self, parameterName, parameter):
        """Set the Parameter with the specified name.

        Parameters:

        parameterName: (string) Name of Parameter to retrieve.

        parameter: (Parameter) New Parameter to use.

        Return value:

        None.

        Description:

        Set the Parameter with the specified name in the list of
        Parameters for this set.
        """
        parameterIndex = self.parameterNameToIndex(parameterName)
        self.setParameterByIndex(parameterIndex, parameter)

    #--------------------------------------------------------------------------

    def parameterNameToIndex(self, parameterName):
        """Map a Parameter name to its index.

        Parameters:

        parameterName: (string) Name of Parameter.

        Return value:

        Index of Parameter with specified name.

        Description:

        Use the specified name to find the index in the list of
        Parameters.
        """
        names = [parameter.getName() for parameter in self._parameters]
        parameterIndex = names.index(parameterName)
        return parameterIndex

    def parameterIndexToName(self, parameterIndex):
        """Map a Parameter index to its name.

        Parameters:

        parameterIndex: (integer) Index of Parameter.

        Return value:

        Name of Parameter with specified index.

        Description:

        Use the specified index to find the name in the list of
        Parameters.
        """
        parameterName = self._parameters[i].getName()
        return parameterName

#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.

if __name__ == '__main__':
    from Parameter import Parameter
    set1 = ParameterSet()
    p0 = Parameter(name = "p0")
    p1 = Parameter(name = "p1")
    p2 = Parameter(name = "p2")
    parameters = [p0, p1, p2]
    set1.setParameters(parameters)
    p = set1.getParameterByName("p0")
    assert str(p) == "Parameter(_free=False,_max=None,_min=None,_name=p0,_scale=1.0,_tagName=parameter,_value=0.0)"
    p = set1.getParameterByIndex(1)
    assert str(p) == "Parameter(_free=False,_max=None,_min=None,_name=p1,_scale=1.0,_tagName=parameter,_value=0.0)"
    p3 = Parameter(name = "p3")
    set1.setParameterByIndex(0, p3)
    p = set1.getParameterByIndex(0)
    assert str(p) == "Parameter(_free=False,_max=None,_min=None,_name=p3,_scale=1.0,_tagName=parameter,_value=0.0)"
    p4 = Parameter(name = "p4")
    set1.setParameterByName("p3", p4)
    p = set1.getParameterByName("p4")
    assert str(p) == "Parameter(_free=False,_max=None,_min=None,_name=p4,_scale=1.0,_tagName=parameter,_value=0.0)"
