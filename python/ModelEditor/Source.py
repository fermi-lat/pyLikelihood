# $Id: Source.py,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

#******************************************************************************

# Import external modules.

# Standard modules.
from copy import deepcopy
import xml.dom.minidom

# Third-party modules.

# Project modules.
from Element import Element
from Spectrum import Spectrum
from SpatialModel import SpatialModel

#******************************************************************************

class Source(Element):
    """Source class to represent <source> elements in ModelEditor.

    Data attributes:

    _name: (string) Name for the Source. Corresponds to the 'name'
    attribute of the <source> element.

    _type: (string) Type string for the Source. Corresponds to the
    'type' attribute of the <source> element.

    _spectrum: (Spectrum) Object containing the spectral model for the
    Source. Corresponds to the child <spectrum> element of the
    <source> element.

    _spatialModel: (SpatialModel) Object containing the spatial model
    for the Source. Corresponds to the child <spatialModel> element of
    the <source> element.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Define the tag name.
    _tagName = 'source'

    # Define attribute defaults.
    _defaultName = 'source'
    _defaultType = 'PointSource'
    _defaultSpectrumType = 'PowerLaw'
    _defaultSpectrum = None
    _defaultSpatialModelType = 'SkyDirFunction'
    _defaultSpatialModel = None

    # Define the valid source types.
    _validTypes = ['PointSource', 'DiffuseSource']

    # Tag name for output grobssim-format source elements.
    _gtobssimSourceElementTagName = 'source'

    # Minimum and maximum energies (MeV) for conversion form
    # ModelEditor to gtobssim source formats.
    _Emin = 30.0
    _Emax = 2.0e5

    #--------------------------------------------------------------------------

    def __init__(self,
                 name         = _defaultName,
                 type         = _defaultType,
                 spectrum     = _defaultSpectrum,
                 spatialModel = _defaultSpatialModel,
                 dom          = None,
                 *args, **kwargs):
        """Initialize this Source.

        Parameters:

        self: This object.

        name: (string) Name for this Source.

        type: (string) Type string for this Source.

        spectrum: (Spectrum) Object containing the spectral model for
        this Source.

        spatialModel: (SpatialModel) Object containing the spatial
        model for this Source.

        dom: (xml.dom.minidom.Element) Object representing a <source>
        element to use when creating this Source. If this parameter is
        provided, the other parameters are ignored.
        """

        # Initialize the parent class. Do not pass the dom argument,
        # since it will be used if needed when fromDom is called
        # below.
        Element.__init__(self, Source._tagName, *args, **kwargs)

        # Set attributes.
        if dom:
            if isinstance(dom, xml.dom.minidom.Element):
                self.fromDom(dom)
            else:
                raise TypeError, 'Not a DOM element (%s)!' % dom
        else:
            self.setName(name)
            self.setType(type)
            if spectrum is None:
                spectrum = Spectrum(type = Source._defaultSpectrumType)
            self.setSpectrum(spectrum)
            if spatialModel is None:
                spatialModel = SpatialModel(type = \
                                            Source._defaultSpatialModelType)
            self.setSpatialModel(spatialModel)

    #--------------------------------------------------------------------------

    def toDom(self, domDocument):
        """Convert this Source to a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this Source (required).

        Return value:

        xml.dom.minidom.Element for this Source.

        Description:

        Convert this Source to an equivalent xml.dom.minidom.Element
        in the specified DOM document. After the DOM element is
        created by the inherited toDom() method, the attribute and
        element nodes are set using the data attributes of this
        Source.
        """

        # Call the inherited method.
        dom = Element.toDom(self, domDocument)

        # Name
        dom.setAttribute('name', self.getName())

        # Type
        dom.setAttribute('type', self.getType())

        # Create and append a DOM element for the child Spectrum.
        spectrum = self.getSpectrum()
        domSpectrum = spectrum.toDom(domDocument)
        dom.appendChild(domSpectrum)

        # Create and append a DOM element for the child SpatialModel.
        spatialModel = self.getSpatialModel()
        domSpatialModel = spatialModel.toDom(domDocument)
        dom.appendChild(domSpatialModel)

        # Return the new DOM element.
        return dom

    def fromDom(self, dom):
        """Initialize this Source from a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        dom (xml.dom.minidom.Element): DOM element to use as the
        source of this Source.

        Return value:

        None.

        Description:

        Use the specified DOM element as the source of the content of
        this Source. Set all data attributes using the corresponding
        attribute and element nodes of the DOM element.
        """

        # Call the inherited method.
        Element.fromDom(self, dom)

        # name
        self.setName(dom.getAttribute('name'))

        # type
        self.setType(dom.getAttribute('type'))

        # <spectrum> element
        domSpectrum = dom.getElementsByTagName('spectrum').item(0)
        spectrum = Spectrum(dom = domSpectrum)
        self.setSpectrum(spectrum)

        # <spatialModel> element
        domSpatialModel = dom.getElementsByTagName('spatialModel').item(0)
        spatialModel = SpatialModel(dom = domSpatialModel)
        self.setSpatialModel(spatialModel)

    #--------------------------------------------------------------------------

    def toObssimDom(self, domDocument):
        """Convert this object to a gtobssim.xsd-compliant XML <source>.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this Source (required).

        Return value:

        xml.dom.minidom.Element of gtobssim.xsd-compliant XML.

        Description:

        Use this Source to create a new xml.dom.minidom.Element for a
        <source> element, using the specified xml.dom.minidom.Document
        object as the owner document. The new element will conform to
        the gtobssim input schema. Return the new DOM element.
        """

        # Fetch the spectrum.
        spectrum = self.getSpectrum()

        # Make sure this is a supported Source type.
        spectrumType = spectrum.getType()
        if spectrumType == 'PowerLaw':
            gtobssimSource = self._powerLaw2Gtobssim(domDocument)
        elif spectrumType == 'BrokenPowerLaw':
            gtobssimSource = self._brokenPowerLaw2Gtobssim(domDocument)
        elif spectrumType == 'PowerLaw2':
            gtobssimSource = self._powerLaw22Gtobssim(domDocument)
        elif spectrumType == 'BrokenPowerLaw2':
            gtobssimSource = self._brokenPowerLaw22Gtobssim(domDocument)
        else:
            raise TypeError, 'Not a supported spectrum type (%s)!' % \
                  spectrumType

        # Return the new DOM element.
        return gtobssimSource

    #--------------------------------------------------------------------------

    def getName(self):
        """Return the name for this Source.

        Parameters:

        self: This object.

        Return value:

        String containing the name for this Source.

        Description:

        Return the name of this Source as a string.
        """
        return self._name

    def setName(self, name):
        """Set the name for this Source.

        Parameters:

        self: This object.

        name (string): New name for this Source.

        Return value:

        None.

        Description:

        Set the name of this Source to the specified string. If the
        new name is invalid, raise a TypeError exception.
        """
        if not self.validName(name):
            raise TypeError, 'Invalid Source name (%s)!' % name
        self._name = str(name)

    def validName(self, name):
        """Check a Source name for validity.

        Parameters:

        self: This object.

        name (string): Proposed name for this Source.

        Return value:

        True if the name is valid, otherwise False.

        Description:

        Check if the proposed new name is valid. A name is valid if
        evaluates to a non-empty string.
        """
        if name is None:
            return False   # str(None) = 'None'
        name = str(name)
        if name == '':
            return False
        return True

    #--------------------------------------------------------------------------

    def getType(self):
        """Return the type for this Source.

        Parameters:

        self: This object.

        Return value:

        String containing the type for this Source.

        Description:

        Return the type for this Source as a string.
        """
        return self._type

    def setType(self, type):
        """Set the type for this Source.

        Parameters:

        self: This object.

        type (string): New type for this Source.

        Return value:

        None.

        Description:

        Set the type of this Source to the specified string. If an
        invalid type is specified, raise a TypeError exception.
        """
        if not self.validType(type):
            raise TypeError, 'Invalid Source type (%s)!' % type
        self._type = type

    def validType(self, type):
        """
        Synopsis:

        Check a type for validity.

        Parameters:

        self: This object.

        type (string): Proposed type for this Source.

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
        """Return the the list of valid Source types.

        Parameters:

        self: This object.

        Return value:

        List of strings containing the valid Source types.

        Description:

        Return the valid types for a Source as a list of strings.
        """
        return Source._validTypes

    #--------------------------------------------------------------------------

    def getSpectrum(self):
        """Return the Spectrum for this Source.

        Parameters:

        self: This object.

        Return value:

        Copy of the Spectrum for this Source.

        Description:

        Return a copy of the Spectrum for this Source.
        """
        return deepcopy(self._spectrum)

    def setSpectrum(self, spectrum):
        """Set the Spectrum for this Source.

        Parameters:

        self: This object.

        spectrum (Spectrum): New Spectrum for this Source.

        Return value:

        None.

        Description:

        Set the Spectrum of this Source to a copy of the specified
        Spectrum. If an invalid Source is specified, raise a TypeError
        exception.
        """
        if not self.validSpectrum(spectrum):
            raise TypeError, 'Invalid Source Spectrum (%s)!' % spectrum
        self._spectrum = deepcopy(spectrum)

    def validSpectrum(self, spectrum):
        """Check a Spectrum for validity.

        Parameters:

        self: This object.

        spectrum (Spectrum): Proposed Spectrum for this Source.

        Return value:

        True if the Spectrum is valid, otherwise False.

        Description:

        Check if the proposed new Spectrum is valid. A Spectrum is
        valid if it is not None. Make this more specific later.
        """
        if spectrum is None:
            return False
        return True

    #--------------------------------------------------------------------------

    def getSpatialModel(self):
        """Return the SpatialModel for this Source.

        Parameters:

        self: This object.

        Return value:

        Copy of the SpatialModel for this Source.

        Description:

        Return a copy of the SpatialModel for this Source.
        """
        return deepcopy(self._spatialModel)

    def setSpatialModel(self, spatialModel):
        """Set the SpatialModel for this Source.

        Parameters:

        self: This object.

        spatialModel (SpatialModel): New SpatialModel for this Source.

        Return value:

        None.

        Description:

        Set the SpatialModel of this Source to a copy of the specified
        SpatialModel. If an invalid Source is specified, raise a TypeError
        exception.
        """
        if not self.validSpatialModel(spatialModel):
            raise TypeError, 'Invalid Source SpatialModel (%s)!' % spatialModel
        self._spatialModel = deepcopy(spatialModel)

    def validSpatialModel(self, spatialModel):
        """Check a SpatialModel for validity.

        Parameters:

        self: This object.

        spatialModel (SpatialModel): Proposed SpatialModel for this Source.

        Return value:

        True if the SpatialModel is valid, otherwise False.

        Description:

        Check if the proposed new SpatialModel is valid. A SpatialModel is
        valid if it is not None. Make this more specific later.
        """
        if spatialModel is None:
            return False
        return True

    #--------------------------------------------------------------------------

    def _powerLaw2Gtobssim(self, gtobssimDocument):

        """Convert a ModelEditor PowerLaw to a gtobssim power law

        Parameters:

        self: This object.

        gtobssimDocument (xml.dom.minidom.Document): DOM document to
        use when converting this Source.

        Return value:

        xml.dom.minidom.Element object for gtobssim.xsd-compliant
        power law source element.

        Description:

        Convert this Source to a gtobssim-format power law source
        element.
        """

        # Save locals.
        Emin = Source._Emin
        Emax = Source._Emax

        # Fetch the spectrum.
        spectrum = self.getSpectrum()

        # Fetch the ModelEditor-format PowerLaw parameters.
        parameter = spectrum.getParameterByName('Prefactor')
        N0 = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('Scale')
        E0 = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('Index')
        g = parameter.getValue() * parameter.getScale()

        # Compute the total flux between Emin and Emax by integrating
        # the distribution between those limits.
        flux = N0 * E0 / (g + 1) * \
               ((Emax / E0)**(g + 1) - (Emin / E0)**(g + 1))

        # Convert the integrated flux from photons/cm^2/s to
        # photons/m^2/s.
        flux *= 1.0e4

        # Create the output DOM element.
        gtobssimSource = \
                       gtobssimDocument.createElement(Source.\
                                                 _gtobssimSourceElementTagName)

        # Set the source name attribute from the input source name.
        gtobssimSource.setAttribute('name', self.getName())
        
        # Set the output flux attribute.
        gtobssimSource.setAttribute('flux', str(flux))

        # Create and append the child <spectrum>.
        gtobssimSpectrum = gtobssimDocument.createElement('spectrum')
        gtobssimSource.appendChild(gtobssimSpectrum)

        # Set the escale attribute of the child <spectrum>.
        gtobssimSpectrum.setAttribute('escale', 'MeV')

        # Create and append the <particle> child of the <spectrum>.
        gtobssimParticle = gtobssimDocument.createElement('particle')
        gtobssimSpectrum.appendChild(gtobssimParticle)

        # Set the <particle> name attribute.
        gtobssimParticle.setAttribute('name', 'gamma')

        # Create and append the child <power_law>.
        gtobssimPowerLaw = gtobssimDocument.createElement('power_law')
        gtobssimParticle.appendChild(gtobssimPowerLaw)

        # Set the <power_law> emin attribute.
        gtobssimPowerLaw.setAttribute('emin', str(Emin))

        # Set the <power_law> gamma attribute.
        gamma = -g
        gtobssimPowerLaw.setAttribute('gamma', str(gamma))

        # Set the <power_law> emax attribute.
        gtobssimPowerLaw.setAttribute('emax', str(Emax))
            
        # Create and append the <celestial_dir> child of the
        # <spectrum>.
        gtobssimCelestialDir = gtobssimDocument.createElement('celestial_dir')
        gtobssimSpectrum.appendChild(gtobssimCelestialDir)

        # Fetch the current spatial model.
        spatialModel = self.getSpatialModel()
        
        # Make sure the spatial model is supported.
        spatialModelType = spatialModel.getType()
        if spatialModelType not in ('SkyDirFunction'):
            raise TypeError, \
                  'Not a supported spatial model type (%s)!' % spatialModelType

        # Set the coordinates of the source.
        parameter = spatialModel.getParameterByName('RA')
        ra = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('ra', str(ra))
        parameter = spatialModel.getParameterByName('DEC')
        dec = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('dec', str(dec))

        # Return the new DOM element.
        return gtobssimSource

    #--------------------------------------------------------------------------

    def _brokenPowerLaw2Gtobssim(self, gtobssimDocument):

        """Convert a BrokenPowerLaw to a gtobssim (broken) power law

        Parameters:

        self: This object.

        gtobssimDocument (xml.dom.minidom.Document): DOM document to
        use when converting this Source.

        Return value:

        xml.dom.minidom.Element object for gtobssim.xsd-compliant
        power law source element.

        Description:

        Convert this Source to a gtobssim-format power law source
        element.
        """

        # Save locals.
        Emin = Source._Emin
        Emax = Source._Emax

        # Fetch the spectrum.
        spectrum = self.getSpectrum()

        # Fetch the ModelEditor-format PowerLaw parameters.
        parameter = spectrum.getParameterByName('Prefactor')
        N0 = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('BreakValue')
        Eb = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('Index1')
        g1 = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('Index2')
        g2 = parameter.getValue() * parameter.getScale()

        # Compute the total flux between Emin and Emax by integrating
        # the distribution between those limits.
        f1 = (1 - (Emin / Eb)**(g1 + 1)) / (g1 + 1)
        f2 = ((Emax / Eb)**(g2 + 1) - 1) / (g2 + 1)
        flux = N0 * Eb * (f1 + f2)

        # Convert the integrated flux from photons/cm^2/s to
        # photons/m^2/s.
        flux *= 1.0e4

        # Create the output DOM element.
        gtobssimSource = \
                       gtobssimDocument.createElement(Source.\
                                                 _gtobssimSourceElementTagName)

        # Set the source name attribute from the input source name.
        gtobssimSource.setAttribute('name', self.getName())

        # Set the output flux attribute.
        gtobssimSource.setAttribute('flux', str(flux))

        # Create and append the child <spectrum>.
        gtobssimSpectrum = gtobssimDocument.createElement('spectrum')
        gtobssimSource.appendChild(gtobssimSpectrum)

        # Set the escale attribute of the child <spectrum>.
        gtobssimSpectrum.setAttribute('escale', 'MeV')

        # Create and append the <particle> child of the <spectrum>.
        gtobssimParticle = gtobssimDocument.createElement('particle')
        gtobssimSpectrum.appendChild(gtobssimParticle)

        # Set the <particle> name attribute.
        gtobssimParticle.setAttribute('name', 'gamma')

        # Create and append the child <power_law>.
        gtobssimPowerLaw = gtobssimDocument.createElement('power_law')
        gtobssimParticle.appendChild(gtobssimPowerLaw)

        # Set the <power_law> emin attribute.
        gtobssimPowerLaw.setAttribute('emin', str(Emin))

        # Set the <power_law> gamma attribute.
        gamma = -g1
        gtobssimPowerLaw.setAttribute('gamma', str(gamma))

        # Set the <power_law> emax attribute.
        gtobssimPowerLaw.setAttribute('emax', str(Emax))

        # Set the <power_law> ebreak attribute.
        gtobssimPowerLaw.setAttribute('ebreak', str(Eb))

        # Set the <power_law> gamma2 attribute.
        gamma2 = -g2
        gtobssimPowerLaw.setAttribute('gamma2', str(gamma2))
            
        # Create and append the <celestial_dir> child of the
        # <spectrum>.
        gtobssimCelestialDir = gtobssimDocument.createElement('celestial_dir')
        gtobssimSpectrum.appendChild(gtobssimCelestialDir)

        # Fetch the current spatial model.
        spatialModel = self.getSpatialModel()
        
        # Make sure the spatial model is supported.
        spatialModelType = spatialModel.getType()
        if spatialModelType not in ('SkyDirFunction'):
            raise TypeError, \
                  'Not a supported spatial model type (%s)!' % spatialModelType

        # Set the coordinates of the source.
        parameter = spatialModel.getParameterByName('RA')
        ra = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('ra', str(ra))
        parameter = spatialModel.getParameterByName('DEC')
        dec = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('dec', str(dec))

        # Return the new DOM element.
        return gtobssimSource

    #--------------------------------------------------------------------------

    def _powerLaw22Gtobssim(self, gtobssimDocument):

        """Convert a PowerLaw2 to a gtobssim power law

        Parameters:

        self: This object.

        gtobssimDocument (xml.dom.minidom.Document): DOM document to
        use when converting this Source.

        Return value:

        xml.dom.minidom.Element object for gtobssim.xsd-compliant
        power law source element.

        Description:

        Convert this Source to a gtobssim-format power law 2 source
        element.
        """

        # Fetch the spectrum.
        spectrum = self.getSpectrum()

        # Fetch the ModelEditor-format PowerLaw parameters.
        parameter = spectrum.getParameterByName('Integral')
        N = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('Index')
        g = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('LowerLimit')
        Emin = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('UpperLimit')
        Emax = parameter.getValue() * parameter.getScale()

        # Compute the total flux between Emin and Emax by integrating
        # the distribution between those limits.
        flux = N

        # Convert the integrated flux from photons/cm^2/s to
        # photons/m^2/s.
        flux *= 1.0e4

        # Create the output DOM element.
        gtobssimSource = \
                       gtobssimDocument.\
                       createElement(Source._gtobssimSourceElementTagName)

        # Set the source name attribute from the input source name.
        gtobssimSource.setAttribute('name', self.getName())
        
        # Set the output flux attribute.
        gtobssimSource.setAttribute('flux', str(flux))

        # Create and append the child <spectrum>.
        gtobssimSpectrum = gtobssimDocument.createElement('spectrum')
        gtobssimSource.appendChild(gtobssimSpectrum)

        # Set the escale attribute of the child <spectrum>.
        gtobssimSpectrum.setAttribute('escale', 'MeV')

        # Create and append the <particle> child of the <spectrum>.
        gtobssimParticle = gtobssimDocument.createElement('particle')
        gtobssimSpectrum.appendChild(gtobssimParticle)

        # Set the <particle> name attribute.
        gtobssimParticle.setAttribute('name', 'gamma')

        # Create and append the child <power_law>.
        gtobssimPowerLaw = gtobssimDocument.createElement('power_law')
        gtobssimParticle.appendChild(gtobssimPowerLaw)

        # Set the <power_law> emin attribute.
        gtobssimPowerLaw.setAttribute('emin', str(Emin))

        # Set the <power_law> gamma attribute.
        gamma = -g
        gtobssimPowerLaw.setAttribute('gamma', str(gamma))

        # Set the <power_law> emax attribute.
        gtobssimPowerLaw.setAttribute('emax', str(Emax))
            
        # Create and append the <celestial_dir> child of the
        # <spectrum>.
        gtobssimCelestialDir = gtobssimDocument.createElement('celestial_dir')
        gtobssimSpectrum.appendChild(gtobssimCelestialDir)

        # Fetch the current spatial model.
        spatialModel = self.getSpatialModel()
        
        # Make sure the spatial model is supported.
        spatialModelType = spatialModel.getType()
        if spatialModelType not in ('SkyDirFunction'):
            raise TypeError, \
                  'Not a supported spatial model type (%s)!' % spatialModelType

        # Set the coordinates of the source.
        parameter = spatialModel.getParameterByName('RA')
        ra = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('ra', str(ra))
        parameter = spatialModel.getParameterByName('DEC')
        dec = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('dec', str(dec))

        # Return the new DOM element.
        return gtobssimSource

    #--------------------------------------------------------------------------

    def _brokenPowerLaw22Gtobssim(self, gtobssimDocument):

        """Convert a BrokenPowerLaww to a gtobssim (broken) power law

        Parameters:

        self: This object.

        gtobssimDocument (xml.dom.minidom.Document): DOM document to
        use when converting this Source.

        Return value:

        xml.dom.minidom.Element object for gtobssim.xsd-compliant
        power law source element.

        Description:

        Convert this Source to a gtobssim-format power law source
        element.
        """

        # Fetch the spectrum.
        spectrum = self.getSpectrum()

        # Fetch the ModelEditor-format PowerLaw parameters.
        parameter = spectrum.getParameterByName('Integral')
        N = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('Index1')
        g1 = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('Index2')
        g2 = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('BreakValue')
        Eb = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('LowerLimit')
        Emin = parameter.getValue() * parameter.getScale()
        parameter = spectrum.getParameterByName('UpperLimit')
        Emax = parameter.getValue() * parameter.getScale()

        # Compute the total flux between Emin and Emax by integrating
        # the distribution between those limits.
        flux = N

        # Convert the integrated flux from photons/cm^2/s to
        # photons/m^2/s.
        flux *= 1.0e4

        # Create the output DOM element.
        gtobssimSource = \
                       gtobssimDocument.\
                       createElement(Source._gtobssimSourceElementTagName)

        # Set the source name attribute from the input source name.
        gtobssimSource.setAttribute('name', self.getName())

        # Set the output flux attribute.
        gtobssimSource.setAttribute('flux', str(flux))

        # Create and append the child <spectrum>.
        gtobssimSpectrum = gtobssimDocument.createElement('spectrum')
        gtobssimSource.appendChild(gtobssimSpectrum)

        # Set the escale attribute of the child <spectrum>.
        gtobssimSpectrum.setAttribute('escale', 'MeV')

        # Create and append the <particle> child of the <spectrum>.
        gtobssimParticle = gtobssimDocument.createElement('particle')
        gtobssimSpectrum.appendChild(gtobssimParticle)

        # Set the <particle> name attribute.
        gtobssimParticle.setAttribute('name', 'gamma')

        # Create and append the child <power_law>.
        gtobssimPowerLaw = gtobssimDocument.createElement('power_law')
        gtobssimParticle.appendChild(gtobssimPowerLaw)

        # Set the <power_law> emin attribute.
        gtobssimPowerLaw.setAttribute('emin', str(Emin))

        # Set the <power_law> gamma attribute.
        gamma = -g1
        gtobssimPowerLaw.setAttribute('gamma', str(gamma))

        # Set the <power_law> emax attribute.
        gtobssimPowerLaw.setAttribute('emax', str(Emax))

        # Set the <power_law> ebreak attribute.
        gtobssimPowerLaw.setAttribute('ebreak', str(Eb))

        # Set the <power_law> gamma2 attribute.
        gamma2 = -g2
        gtobssimPowerLaw.setAttribute('gamma2', str(gamma2))
            
        # Create and append the <celestial_dir> child of the
        # <spectrum>.
        gtobssimCelestialDir = gtobssimDocument.createElement('celestial_dir')
        gtobssimSpectrum.appendChild(gtobssimCelestialDir)

        # Fetch the current spatial model.
        spatialModel = self.getSpatialModel()
        
        # Make sure the spatial model is supported.
        spatialModelType = spatialModel.getType()
        if spatialModelType not in ('SkyDirFunction'):
            raise TypeError, \
                  'Not a supported spatial model type (%s)!' % spatialModelType

        # Set the coordinates of the source.
        parameter = spatialModel.getParameterByName('RA')
        ra = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('ra', str(ra))
        parameter = spatialModel.getParameterByName('DEC')
        dec = parameter.getValue() * parameter.getScale()
        gtobssimCelestialDir.setAttribute('dec', str(dec))

        # Return the new DOM element.
        return gtobssimSource

#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.

if __name__ == '__main__':

    # Default constructor.
    source = Source()
    assert str(source) == 'Source(_name=source,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw),_tagName=source,_type=PointSource)'

    # Constructor with attribute values.
    spectrum = Spectrum()
    spatialModel = SpatialModel()
    source = Source(name = 'source 1', type = 'PointSource',
                    spectrum = spectrum, spatialModel = spatialModel)
    assert str(source) == 'Source(_name=source 1,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=False,_max=10.0,_min=0.0,_name=Value,_scale=1.0,_tagName=parameter,_value=1.0)],_tagName=spectrum,_type=ConstantValue),_tagName=source,_type=PointSource)'

    # Convert to/from DOM object.
    import xml.dom.minidom
    domDocument = xml.dom.minidom.Document()
    domSource = source.toDom(domDocument)
    sourceCopy = Source(dom = domSource)
    assert sourceCopy == source
    assert not (sourceCopy != source)

    # Convert to a gtobssim-compliant power law element.
    source = Source()
    gtobssimSource = source.toObssimDom(domDocument)

    # Convert to a gtobssim-compliant broken power law element.
    spectrum = Spectrum(type = 'BrokenPowerLaw')
    source = Source(spectrum = spectrum)
    gtobssimSource = source.toObssimDom(domDocument)

    # Convert to a gtobssim-compliant power law 2 element.
    spectrum = Spectrum(type = 'PowerLaw2')
    source = Source(spectrum = spectrum)
    gtobssimSource = source.toObssimDom(domDocument)

    # Convert to a gtobssim-compliant broken power law 2 element.
    spectrum = Spectrum(type = 'BrokenPowerLaw2')
    source = Source(spectrum = spectrum)
    gtobssimSource = source.toObssimDom(domDocument)
