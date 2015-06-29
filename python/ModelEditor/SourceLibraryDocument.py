# $Id: SourceLibraryDocument.py,v 1.2.6.1 2014/03/07 18:06:52 jasercio Exp $

#******************************************************************************

# Import external modules.

# Standard modules.
from copy import deepcopy
import xml.dom.minidom

# Third-party modules.

# Project modules.
from SourceLibrary import SourceLibrary

#******************************************************************************

class SourceLibraryDocument():
    """SourceLibraryDocument class to represent documents which conform to the source_library.xsd schema.

    Attributes:

    _source_library: (SourceLibrary) Object for the root element in
    the document.
    """

    #--------------------------------------------------------------------------

    # Class constants

    # Default attributes.
    _defaultSourceLibrary = SourceLibrary()

    #--------------------------------------------------------------------------

    def __init__(self,
                 sourceLibrary = _defaultSourceLibrary,
                 dom           = None,
                 path          = None):
        """Initialize this SourceLibraryDocument.

        Parameters:

        sourceLibrary: (SourceLibrary) Object for root
        <source_library> element.

        dom: (xml.dom.minidom.Document) Object representing a XML
        document which conforms to the source_library.xsd schema. If
        dom is specified and path is not specified, the other
        arguments are ignored.

        path: (string) Path to an XML file conforming to the
        source_library.xsd schema from which to read the source
        library description. If path is specified, the other arguments
        are ignored.
        """

        # Set attributes.
        if path:
            self.fromFile(path)
        elif dom:
            self.fromDom(dom)
        else:
            self.setSourceLibrary(sourceLibrary)

    #--------------------------------------------------------------------------

    def __str__(self):
        """Return a string version of this SourceLibraryDocument.

        Parameters:

        self: This object.

        Return value:

        String representation of this SourceLibraryDocument.

        Description:

        Compute and return a string representation of this
        SourceLibraryDocument. Used whenever the SourceLibraryDocument
        is evaluated in a string context, e.g. in a print statement.
        """
        s = 'SourceLibraryDocument(source_library=%s)' % \
            self.getSourceLibrary()
        return s

    #--------------------------------------------------------------------------

    def __eq__(self, other):
        """Compare this and another SourceLibraryDocument for equality.

        Parameters:

        self: This object.

        other (SourceLibraryDocument): SourceLibraryDocument to
        compare against for equality.

        Return value:

        True if equal, False otherwise.

        Description:

        Compare the current SourceLibraryDocument to another
        SourceLibraryDocument for equality. Used by the '==' operator.
        The equality check is relatively expensive - it converts both
        objects to strings and compares the strings. This was done for
        simplicity. A more efficient method may be implemented if
        needed.
        """

        # Return True if the objects are the same object.
        if self is other:
            return True

        # Return False if the string representations are not equal.
        if str(self) != str(other):
            return False

        # The objects are equal.
        return True

    #--------------------------------------------------------------------------

    def __ne__(self, other):
        """Compare this and another SourceLibraryDocument for inequality.

        Parameters:

        self: This object.

        other (SourceLibraryDocument): SourceLibraryDocument to
        compare against for inequality.

        Return value:

        True if unequal, False otherwise.

        Description:

        Compare the current SourceLibraryDocument to another
        SourceLibraryDocument for inequality. Used by the '!='
        operator. The inequality check is relatively expensive - it
        converts both objects to strings and compares the strings.
        This was done for simplicity. A more efficient method may be
        implemented if needed.
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

    def toDom(self):
        """Convert this SourceLibraryDocument to a xml.dom.minidom.Document.

        Parameters:

        self: This object.

        Return value:

        xml.dom.minidom.Document for this SourceLibraryDocument.

        Description:

        Convert this SourceLibraryDocument to an equivalent
        xml.dom.minidom.Document.
        """

        # Create the new DOM Document object.
        domDocument = xml.dom.minidom.Document()

        # Convert the SourceLibrary object to a DOM Element object.
        sourceLibrary = self.getSourceLibrary()
        domElement = sourceLibrary.toDom(domDocument)

        # Attach the new element to the new document.
        domDocument.appendChild(domElement)

        # Return the new Document object.
        return domDocument

    def fromDom(self, dom):
        """Initialize this SourceLibraryDocument from a xml.dom.minidom.Document.

        Parameters:

        self: This object.

        dom (xml.dom.minidom.Document): DOM document to use as the
        source of this SourceLibraryDocument.

        Return value:

        None.

        Description:

        Use the specified DOM document as the source of the content of
        this SourceLibraryDocument.
        """

        # Find the root element for this document.
        sourceLibraryElement = dom.documentElement

        # Convert the root element to a SourceLibrary.
        sourceLibrary = SourceLibrary(dom = sourceLibraryElement)

        # Save the converted <source_library> element.
        self.setSourceLibrary(sourceLibrary)

    #--------------------------------------------------------------------------

    def toObssimDom(self):
        """Convert this object to a gtobssim.xsd-compliant XML document.

        Parameters:

        self: This object.

        Return value:

        xml.dom.minidom.Document of gtobssim.xsd-compliant XML.

        Description:

        Convert this SourceLibraryDocument to an equivalent
        gtobssim.xsd-compliant XML document.
        """

        # Create the new DOM Document object.
        domDocument = xml.dom.minidom.Document()

        # Convert the SourceLibrary object to a DOM Element object.
        sourceLibrary = self.getSourceLibrary()
        domElement = sourceLibrary.toObssimDom(domDocument)

        # Attach the new element to the new document.
        domDocument.appendChild(domElement)

        # Return the new DOM docment.
        return domDocument

    #--------------------------------------------------------------------------

    def getSourceLibrary(self):
        """Return a copy of the SourceLibrary for this SourceLibraryDocument.

        Parameters:

        self: This object.

        Return value:

        Copy of SourceLibrary for this SourceLibraryDocument.

        Description:

        Return a copy of the SourceLibrary for this
        SourceLibraryDocument.
        """
        return deepcopy(self._sourceLibrary)

    def setSourceLibrary(self, sourceLibrary):
        """Set the SourceLibrary for this SourceLibraryDocument.

        Parameters:

        self: This object.

        sourceLibrary (SourceLibrary): SourceLibrary to use for this
        SourceLibraryDocument.

        Return value:

        None.

        Description:

        Set the SourceLibrary for this SourceLibraryDocument to a copy
        of the specified SourceLibrary. If the new SourceLibrary is
        invalid, raise a TypeError exception.
        """
        if not self.validSourceLibrary(sourceLibrary):
            raise TypeError, \
                  'Invalid SourceLibraryDocument SourceLibrary (%s)!' \
                  % sourceLibrary
        self._sourceLibrary = deepcopy(sourceLibrary)

    def validSourceLibrary(self, sourceLibrary):
        """Check a SourceLibrary for validity.

        Parameters:

        self: This object.

        sourceLibrary (SourceLibrary): Proposed SourceLibrary for this
        SourceLibraryDocument.

        Return value:

        True if the SourceLibrary is valid, otherwise False.

        Description:

        Check if the proposed SourceLibrary is valid. A SourceLibrary
        is valid if it is not None (improve this later).
        """
        if sourceLibrary is None:
            return False
        return True

    #--------------------------------------------------------------------------

    def fromFile(self, path):
        """Read the SourceLibraryDocument from a XML file.

        Parameters:

        self: This object.

        path (string): Path to XML file.

        Return value:

        None.

        Description:

        Parse the specified file and use it for the content of this
        SourceLibraryDocument object.
        """

        # Parse the XML document.
        dom = xml.dom.minidom.parse(path)

        # Initialize the object with the DOM document.
        self.fromDom(dom)

    def toFile(self, path):
        """Write this SourceLibraryDocument to the specified XML file.

        Parameters:

        self: This object.

        path (string): Path to XML file.

        Return value:

        None.

        Description:

        Write the current document to the specified file as XML.
        """

        # Create the output file.
        out = open(path, 'w')
        
        # Convert the object to a DOM Document object.
        domDocument = self.toDom()
        
        # Write the XML to the output file.
        domDocument.writexml(out, indent = '', addindent = '  ', newl = '\n')
        
        # Close the output file.
        out.close()

    #--------------------------------------------------------------------------

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
        self._sourceLibrary.addSource(source)

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
        self._sourceLibrary.removeSource(sourceIndex)

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
        return self._sourceLibrary.getNumSources()

    #--------------------------------------------------------------------------

    def sortSources(self,params):
        """ Sort the source list
        
        Parameters:
        - self - This object
        - params - Dictionary of sort parameters.  See SourceLibrary.sort() for details
                   of content.
        
        Return value:
        - none
        
        Description:
            This method just passes the sort command through to the SourceLibrary itself.
        See the SourceLibrary().sort() method for a full description
        """       
        self._sourceLibrary.sort(params)

#******************************************************************************

# Self-test code.

# If this code generates any output, an error has been found.


if __name__ == '__main__':

    # Default constructor.
    sourceLibraryDocument = SourceLibraryDocument()

    # Constructor with attribute values.
    sourceLibrary = SourceLibrary()
    sourceLibraryDocument = SourceLibraryDocument(sourceLibrary = sourceLibrary)
    assert str(sourceLibraryDocument) == 'SourceLibraryDocument(source_library=SourceLibrary(_sources=[Source(_name=source,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw),_tagName=source,_type=PointSource)],_tagName=source_library,_title=Source Library))'

    # Add a new Source.
    from Source import Source
    sourceLibraryDocument.addSource(Source())
    assert str(sourceLibraryDocument) == 'SourceLibraryDocument(source_library=SourceLibrary(_sources=[Source(_name=source,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw),_tagName=source,_type=PointSource),Source(_name=source,_spatialModel=SpatialModel(_file=None,_parameters=[Parameter(_free=False,_max=360.0,_min=0.0,_name=RA,_scale=1.0,_tagName=parameter,_value=0.0),Parameter(_free=False,_max=90.0,_min=-90.0,_name=DEC,_scale=1.0,_tagName=parameter,_value=0.0)],_tagName=spatialModel,_type=SkyDirFunction),_spectrum=Spectrum(_file=None,_parameters=[Parameter(_free=True,_max=1000.0,_min=0.001,_name=Prefactor,_scale=1e-09,_tagName=parameter,_value=1.0),Parameter(_free=True,_max=-1.0,_min=-5.0,_name=Index,_scale=1.0,_tagName=parameter,_value=-2.1),Parameter(_free=False,_max=2000.0,_min=30.0,_name=Scale,_scale=1.0,_tagName=parameter,_value=100.0)],_tagName=spectrum,_type=PowerLaw),_tagName=source,_type=PointSource)],_tagName=source_library,_title=Source Library))'

    # Check the source count method.
    assert sourceLibraryDocument.getNumSources() == 2

    # Remove the newly-added Source.
    sourceLibraryDocument.removeSource(1)
    assert sourceLibraryDocument.getNumSources() == 1

    # Convert to/from DOM object.
    dom = sourceLibraryDocument.toDom()
    sourceLibraryDocumentCopy = SourceLibraryDocument(dom = dom)
    assert sourceLibraryDocumentCopy == sourceLibraryDocument
    assert not (sourceLibraryDocumentCopy != sourceLibraryDocument)

    # Read from a file.
    sourceLibraryDocument = SourceLibraryDocument(path = 'test.xml')

    # Write to a file.
    sourceLibraryDocument.toFile('test_out.xml')
    from os import remove
    remove('test_out.xml')

    # Create a gtobssim-compliant power law element.
    sourceLibrary = SourceLibrary()
    sourceLibraryDocument = SourceLibraryDocument(sourceLibrary = sourceLibrary)
    obssimDom = sourceLibraryDocument.toObssimDom()
