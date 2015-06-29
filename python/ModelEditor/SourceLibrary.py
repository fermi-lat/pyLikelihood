# $Id: SourceLibrary.py,v 1.4.6.1 2014/03/07 18:06:52 jasercio Exp $

#******************************************************************************

# Import external modules.

# Standard modules.
from copy import deepcopy
import xml.dom.minidom

# Third-party modules.

# Project modules.
from Element import Element
from Source import Source
from CatalogSourceExtractor import angsep


#******************************************************************************

class SourceLibrary(Element):
    """SourceLibrary class to represent <source_library> elements in ModelEditor

    Attributes:

    _title: (string) Title for the SourceLibrary. Corresponds to the
    'title' attribute of the <source_library> element.

    _sources: (list of Source) One or more Sources which define the
    SourceLibrary. Corresponds to the sequence of 1 or more child
    <source> elements of the <source_library> element.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Define the tag name.
    _tagName = 'source_library'

    # Default attributes.
    _defaultXmlns = "http://fermi.gsfc.nasa.gov/source_library"
    _defaultTitle = 'Source Library'
    _defaultSources = None

    #--------------------------------------------------------------------------

    def __init__(self,
                 title   = _defaultTitle,
                 sources = _defaultSources,
                 dom     = None):
        """Initialize this SourceLibrary.

        Parameters:

        self: This object.

        title: (string) Title for this SourceLibrary.

        sources: (list of Source) One or more Sources which define the
        SourceLibrary.

        dom: (xml.dom.minidom.Element) Object representing a
        <source_library> element to use when creating the new
        SourceLibrary. If this parameter is provided, the other
        parameters are ignored.
        """

        # Initialize the parent class. Do not pass the dom argument,
        # since it will be used if needed when fromDom is called
        # below.
        Element.__init__(self, tagName = SourceLibrary._tagName)

        # Set attributes.
        if dom:
            if isinstance(dom, xml.dom.minidom.Element):
                self.fromDom(dom)
            else:
                raise TypeError, 'Not a DOM element (%s)!' % dom
        else:
            self.setXmlns(SourceLibrary._defaultXmlns)
            self.setTitle(title)
            if sources is None or len(sources) == 0:
                sources = [Source()]
            self.setSources(sources)

    #--------------------------------------------------------------------------

    def toDom(self, domDocument):
        """Convert this SourceLibrary to a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this SourceLibrary (required).

        Return value:

        xml.dom.minidom.Element for this SourceLibrary.

        Description:

        Convert this SourceLibrary to an equivalent
        xml.dom.minidom.Element in the specified DOM document. After
        the DOM element is created by the inherited toDom() method,
        the attribute and element nodes are set using the data
        attributes of this SourceLibrary.
        """
        
        # Call the inherited method.
        dom = Element.toDom(self, domDocument)

        # XML namespace
        dom.setAttribute('xmlns', self.getXmlns())

        # Title
        dom.setAttribute('title', self.getTitle())

        # Create and append a DOM element for each child Source.
        for source in self.getSources():
            domElement = source.toDom(domDocument)
            dom.appendChild(domElement)

        # Return the new DOM element.
        return dom

    def fromDom(self, dom):
        """Initialize this SourceLibrary from a xml.dom.minidom.Element.

        Parameters:

        self: This object.

        dom (xml.dom.minidom.Element): DOM element to use as the
        source of this SourceLibrary.

        Return value:

        None.

        Description:

        Use the specified DOM element as the source of the content of
        this SourceLibrary. Set all data attributes using the
        corresponding attribute and element nodes of the DOM element.
        """

        # Call the inherited method.
        Element.fromDom(self, dom)

        # XML namespace (if valid)
        xmlns = dom.getAttribute('xmlns');
        if self.validXmlns(xmlns):
            self.setXmlns(xmlns)

        # Title
        self.setTitle(dom.getAttribute('title'))

        # Copy the child <source> elements.
        sources = [Source(dom = domElement) for domElement in
                   dom.getElementsByTagName('source')]
        self.setSources(sources)

    #--------------------------------------------------------------------------

    def toObssimDom(self, domDocument):
        """Convert this object to a gtobssim.xsd-compliant XML <source_library>.

        Parameters:

        self: This object.

        domDocument (xml.dom.minidom.Document): DOM document to use
        when converting this SourceLibrary (required).

        Return value:

        xml.dom.minidom.Element of gtobssim.xsd-compliant XML.

        Description:

        Convert this SourceLibrary to an equivalent
        gtobssim.xsd-compliant XML element.
        """

        # Call the inherited method.
        dom = Element.toDom(self, domDocument)

        # Title
        title = self.getTitle()
        dom.setAttribute('title', title)

        # Convert each child <source> element.
        for source in self.getSources():
            domSource = source.toObssimDom(domDocument)
            dom.appendChild(domSource)

        # Return the new DOM element.
        return dom

    #--------------------------------------------------------------------------

    def getXmlns(self):
        """Return the XML namespace for this SourceLibrary.

        Parameters:

        self: This object.

        Return value:

        String containing the XML namespace for this SourceLibrary.

        Description:

        Return the XML namespace of this SourceLibrary as a string.
        """
        return self._xmlns

    def setXmlns(self, xmlns):
        """Set the XML namespace for this SourceLibrary.

        Parameters:

        self: This object.

        xmlns (string): New XML namespace for this SourceLibrary.

        Return value:

        None.

        Description:

        Set the XML namespace of this SourceLibrary to the specified string.
        If the new XML namespace is invalid, raise a TypeError exception.
        """
        if not self.validXmlns(xmlns):
            raise TypeError, 'Invalid SourceLibrary xmlns (%s)!' % xmlns
        self._xmlns = str(xmlns)

    def validXmlns(self, xmlns):
        """Check a SourceLibrary XML namespace for validity.

        Parameters:

        self: This object.

        xmlns (string): Proposed XML namespace for this SourceLibrary.

        Return value:

        True if the XML namespace is valid, otherwise False.

        Description:

        Check if the proposed new XML namespace is valid. A XML
        namespace is valid if evaluates to a non-empty string.
        """
        if xmlns is None:
            return False   # str(None) = 'None'
        xmlns = str(xmlns)
        if xmlns == '':
            return False
        return True

    #--------------------------------------------------------------------------

    def getTitle(self):
        """Return the title for this SourceLibrary.

        Parameters:

        self: This object.

        Return value:

        String containing the title for this SourceLibrary.

        Description:

        Return the title of this SourceLibrary as a string.
        """
        return self._title

    def setTitle(self, title):
        """Set the title for this SourceLibrary.

        Parameters:

        self: This object.

        title (string): New title for this SourceLibrary.

        Return value:

        None.

        Description:

        Set the title of this SourceLibrary to the specified string.
        If the new title is invalid, raise a TypeError exception.
        """
        if not self.validTitle(title):
            raise TypeError, 'Invalid SourceLibrary title (%s)!' % title
        self._title = str(title)

    def validTitle(self, title):
        """Check a SourceLibrary title for validity.

        Parameters:

        self: This object.

        title (string): Proposed title for this SourceLibrary.

        Return value:

        True if the title is valid, otherwise False.

        Description:

        Check if the proposed new title is valid. A title is valid if
        evaluates to a non-empty string.
        """
        if title is None:
            return False   # str(None) = 'None'
        title = str(title)
        if title == '':
            return False
        return True

    #--------------------------------------------------------------------------

    def getSources(self):
        """Return a copy of the list of Sources for this SourceLibrary

        Parameters:

        self: This object.

        Return value:

        Copy of list of Sources for this SourceLibrary.

        Description:

        Return a copy of the list of Sources for this SourceLibrary.
        """
        return deepcopy(self._sources)

    def setSources(self, sources):
        """Set the list of Sources for this SourceLibrary.

        Parameters:

        self: This object.

        sources (list of Source): List of Sources to use for this SourceLibrary

        Return value:

        None.

        Description:

        Set the list of Sources for this SourceLibrary to a copy of
        the specified list. If the new Sources are invalid, raise a
        TypeError exception.
        """
        if not self.validSources(sources):
            raise TypeError, 'Invalid SourceLibrary Sources (%s)!' % \
                  ','.join(str(s) for s in sources)
        self._sources = deepcopy(sources)

    def validSources(self, sources):
        """Check a Source list for validity.

        Parameters:

        self: This object.

        sources (list of Source): Proposed Sources for this SourceLibrary.

        Return value:

        True if the source list is valid, otherwise False.

        Description:

        Check if the proposed Source list is valid. A
        Source list is valid if it contains at least 1 Source.
        """
        if len(sources) == 0:
            return False
        return True

    def getNumSources(self):
        """Return the number of Sources.

        Parameters:

        self: This object.

        Return value:

        Integer containing the number of Sources in this
        SourceLibrary.

        Description:

        Return the number of Sources in this SourceLibrary.
        """
        return len(self._sources)

    def addSource(self, source):
        """Append a copy of the specified Source to the list of Sources.

        Parameters:

        self: This object.

        source (Source): New Source to append.

        Return value:

        None

        Description:

        Append a copy of the specified Source to the list of Sources for
        this SourceLibrary.
        """
        self._sources.append(deepcopy(source))

    def removeSource(self, sourceIndex):
        """Remove the specified Source from the list of Sources.

        Parameters:

        self: This object.

        sourceIndex (integer): Index of Source to remove.

        Return value:

        None

        Description:

        Remove the specified Source from the list of Sources.
        """
        del self._sources[sourceIndex]

    #--------------------------------------------------------------------------

    def sort(self,params):
        """ Sort the source list
        
        Parameters:
        - self - This object
        - params - Dictionary of sorting parameters containing the following keys:
            - sortType - (required) The type of sort to perform (can be one of Name, Position, 
                         Center, SpectralType, SourceType, Index, or Flux)
            - ascending - (required) Flag for whether the sort should be ascending or descending
            - ra - (optional) RA of the center of region of interest - used for "Center" searches
            - dec - (optional) Dec of the center of region of interest - used for "Center" searches
        
        Return value:
        - none
        
        Description:
            This method looks at the sortType parameters and chooses the appropriate sorting method
        to use on the data.  Sorts are done on a copy of the source list and then the new sorted list
        is stored in place of the original list.  In some cases the sorts can be done directly.
        However, in other cases, a helper method is called to guard against exceptions that can occur
        when the parameter being sorted on is not present in all sources.  Sources without the sort
        parameter should be sorted to the bottom of the list.
        """
#        print "performing a", params['sortType'], "sort, ascending =", params['ascending']

        sources = self.getSources()
        if ("Name" == params['sortType']):
            sources.sort(key=lambda src: src.getName().lower(),reverse = not params['ascending'])
        elif ("Position" == params['sortType']):
            sources.sort(key=lambda src: self._getSpatialKey(src,'DEC'), reverse = not params['ascending'])
            sources.sort(key=lambda src: self._getSpatialKey(src,'RA'), reverse = not params['ascending'])
        elif ("Center" == params['sortType']):
            sources.sort(key = lambda src: self._getAngsep(src,params['ra'], params['dec']),
                         reverse = not params['ascending'])
        elif ("SpectralType" == params['sortType']):
            sources.sort(key=lambda src: src.getSpectrum().getType(), reverse = not params['ascending'])
        elif ("SourceType" == params['sortType']):
            sources.sort(key=lambda src: src.getType(), reverse = not params['ascending'])
        elif ("Index" == params['sortType']):
            sources.sort(key=lambda src: self._getIndex(src), reverse = not params['ascending'])
        elif ("Flux" == params['sortType']):
            sources.sort(key=lambda src: self._getIntegralFlux(src), reverse = not params['ascending'])
        else:
            print "Specified sort type not implemented"
            
        self.setSources(sources)  #store sorted source list
        
    def _getSpatialKey(self,src,key):
        """ Provide position values from the source's spatial model
        
        Parameters:
        - self - This object
        - src - The source object to extract values from
        - key - The parameter Name to get the value from, one of "RA" or "DEC"
        
        Return value:
        - The value of the specified parameter or 361 if the parameter doesn't exist
        
        Description:
            This function returns the value of the specified parameter from the given source to allow
        for sorting on the specified parameter.  As not all sources have a spatial model with RA and
        Dec, this method is used as a sorting key and guards against exceptions when the RA and DEC
        parameters are not present.  In those cases it returns a value of 361 which will place these
        sources at the end of the list (or the front if the sort is descending).  Note: would have used
        a None object but in sorting that ends up first instead of last. 
        """
        try:
            value=src.getSpatialModel().getParameterByName(key).getValue()
        except:
            value = 361  #return a value that will be higher than any true value so source without the value are at the end.  A None object gets sorted first
        return value
    
    def _getIndex(self,src):
        """ Provide primary spectral index from the source's spectral model
        
        Parameters:
        - self - This object
        - src - The source object to extract values from
        
        Return value:
        - The value of the primary spectral index or 999 if the parameter doesn't exist
        
        Description:
            This function returns the value of the primary spectral index from the given source to allow
        for sorting.  As not all sources have a spectral model with an index parameter, this method is 
        used as a sorting key and guards against exceptions when the a spectral index
        parameter is not present.  In those cases it returns a value of 99 which will place these
        sources at the end of the list (or the front if the sort is descending).  It also handles the
        fact that the primary index has different names in different spectral models and checks for each
        of them in turn.
        """
        try:
            # check the PowerLaw, PowerLaw2, and ExoCutOff source types
            value=src.getSpectrum().getParameterByName("Index").getValue()  
        except:
            try:
                # check the BrokenPowerLaw, BrokenPowerLaw2, BrokenPowerLawExpCutoff, PLSuperExpCutoff, and SmoothBrokenPowerLaw source types
                value=src.getSpectrum().getParameterByName("Index1").getValue()
            except:
                try:
                    # check the LogParabola and BandFunction source types
                    value=src.getSpectrum().getParameterByName("alpha").getValue()
                except:
                    value = 999  # If none of the above match, return a value that will be higher than any true value 
                                 # so sources without an index value are at the end.
        return value
    
    def _getIntegralFlux(self,src):
        """ Provide Integral parameter value from the source's spectral model
        
        Parameters:
        - self - This object
        - src - The source object to extract values from
        
        Return value:
        - The value of the Integral or 9e99 if the parameter doesn't exist
        
        Description:
            This function returns the value of the Integral parameter from the given source to allow
        for sorting.  As not all sources have a spectral model with an Integral parameter, this method is 
        used as a sorting key and guards against exceptions when the Integral parameter is not present.  
        In those cases it returns a value of 9e99 which will place these
        sources at the end of the list (or the front if the sort is descending).
        """
        try:
            # check the PowerLaw, PowerLaw2, and ExoCutOff source types
            value=src.getSpectrum().getParameterByName("Integral").getValue()  
        except:
            value = 9e99  # If none of the above match, return a value that will be higher than any true value 
                          # so sources without an Integral value are at the end.
        return value
    
    def _getAngsep(self,src,ra,dec):
        """ Provide position values from the source's spatial model
        
        Parameters:
        - self - This object
        - src - The source object to extract values from
        - ra - The RA of the ROI center
        - dec - The Dec of the ROI center
        
        Return value:
        - The angular distance to the source from the ROI center or 361 if no source RA and Dec available
        
        Description:
            This function returns the angular separation of the given source to the ROI center to allow
        for sorting on the distance.  As not all sources have a spatial model with RA and
        Dec, this method is used as a sorting key and guards against exceptions when the RA and DEC
        parameters are not present.  In those cases it returns a value of 361 which will place these
        sources at the end of the list (or the front if the sort is descending).
        """
        ra2 = self._getSpatialKey(src,'RA')
        dec2 = self._getSpatialKey(src,'DEC')
        if (361 == ra2 or 361 == dec2): return 361
        return angsep(ra,dec,ra2,dec2)
    
#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.

if __name__ == '__main__':

    # Default constructor.
    sourceLibrary = SourceLibrary()

    # Constructor with attribute values.
    source = Source()
    sourceLibrary = SourceLibrary(title = 'library 1', sources = [source])
    assert str(sourceLibrary) == 'SourceLibrary(_sources=[Source(_name=source,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw),_tagName=source,_type=PointSource)],_tagName=source_library,_title=library 1)'

    # Add a new Source.
    sourceLibrary.addSource(Source())
    assert str(sourceLibrary) == 'SourceLibrary(_sources=[Source(_name=source,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw),_tagName=source,_type=PointSource),Source(_name=source,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw),_tagName=source,_type=PointSource)],_tagName=source_library,_title=library 1)'

    # Check the source count method.
    assert sourceLibrary.getNumSources() == 2

    # Remove the newly-added Source.
    sourceLibrary.removeSource(1)
    assert sourceLibrary.getNumSources() == 1

    # Convert to/from DOM object.
    import xml.dom.minidom
    domDocument = xml.dom.minidom.Document()
    dom = sourceLibrary.toDom(domDocument)
    sourceLibraryCopy = SourceLibrary(dom = dom)
    assert sourceLibraryCopy == sourceLibrary
    assert not (sourceLibraryCopy != sourceLibrary)

    # Create a gtobssim-compliant power law element.
    sourceLibrary = SourceLibrary()
    domDocument = xml.dom.minidom.Document()
    obssimDom = sourceLibrary.toObssimDom(domDocument)

