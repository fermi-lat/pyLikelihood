# $Id$

#******************************************************************************

# Import external modules.

# Standard modules
from tkMessageBox import showerror

# Third-party modules
import pyfits
from numpy import floor,log10,cos,sin,arccos,pi,array,log

# Project modules
from Source import Source
from Parameter import Parameter
from Spectrum import Spectrum
from SpatialModel import SpatialModel
from FitsFile import FitsFile

# set up some aliases and constants
acos=arccos
d2r=pi/180.

#******************************************************************************

class CatalogSourceExtractor():
    """Class to extract sources from the Fermi LAT catalogs

    This class implements Tyrel's make2FGLxml script inside the modeleditor to
    extract the catalog entries and add them as sources to the model file.

    To invoke this class, you must pass in a dictionary containing the information
    on the location of the source catalog file, the FT1 event file, the galactic
    diffuse and isotropic template files, the names of the models to use from the
    latter two files, the significance limit for the sources to be extracted
    from the catalog file, a radius within which to allow sources to vary, and a
    flag to indicate whether or not to force extended sources to be treated as
    point sources.  The full details of this dictionary are given in
    the AddCatalogSourcesDialog.py file.

    The class selects all sources that are within the extraction area of the
    supplied FT1 event file plus all sources in an annulus 5 degrees around
    the extraction area to include sources that might bleed into the ROI.

    Usage:
         extractor = CatalogSourceExtractor(catalogParameters)
         sources = extractor.getSources()


    """

    def __init__(self,catParams = None):
        """Initialize the class

        Parameters:
        - self - This CatalogSourceExtractor object
        - catParams - A dictionary (created by the AddCatalogSourcesDialog object)
                      listing the relevant files and parameters for extracting the
                      catalog sources

        Return value:
        - none

        Description:
        """
        self.sources = None
        if (None == catParams):
            showerror("Model Extraction Error","No catalog data parameters provided.  Unable to add sources")
            return
        self.catParams = catParams
#        self._headerNum=1


    def getSources(self):
        """Public method to retrieve the source list

        Parameters:
        - self - This CatalogSourceExtractor object

        Return value:
        - self.sources - A list of Source objects representing the various sources
                         to be added to the model
        - self.ra - RA of ROI center
        - self.dec - Dec of ROI center

        Description:

        """
        #Validate FT1 file
        self.FT1File = FitsFile(self.catParams['eventFile'])
        if (None == self.FT1File.getType() or not self.FT1File.hasROIData()):
            return None,0,0

        #Validate Galactic diffuse file if present
        #Validate isotropic template file if present

        # get ROI information
        self.ra,self.dec,self.radius = self.FT1File.getROIData()
        # set radius limit
        self.radLim=(self.radius if self.catParams['radiusLimit']<=0 else self.catParams['radiusLimit'])

        self.catFile = FitsFile(self.catParams['catalogFile'])
        # Generate source list
        if('1FGL' == self.catFile.getType()):
            self._add1FGLSources()
        elif ('2FGL' == self.catFile.getType()):
            self._add2FGLSources()
        elif ('3FGL' == self.catFile.getType()):
            self._add3FGLSources()
        else:
            showerror("File Error","Specified catalog file is not valid")

        return self.sources, self.ra, self.dec

#     def _validateFT1File(self):
#         """ Check that the passed in FT1 file contains the necessary information
#
#         This method opens the FT1 file listed in the 'eventFile' entry of the
#         self.catParams dictionary.  If the file is present, and contains the ROI
#         information then the opened file object is returned.  If not, a None object
#         is returned.
#
#         Usage:
#             eventFile = self._validateFT1File()
#             if (None == eventFile):
#                 #handle error here
#
#         Adapted from the mak2FGLxml.getPos() method by Tyrel Johnson
#         """
#         try:
#             FT1File = pyfits.open(self.catParams['eventFile'])
#         except:  # we get here only if the file doesn't even exist
#             showerror("File Not Found", "Specified event file doesn't exist.")
#             return None
#         if ([] == FT1File):  #the file either didn't exist or was not a valid FITS file
#             showerror("Bad File Type", "Specified event file is not a valid FITS file.")
#             return None
#
#         # check to see if the POS keyword exists
#         try:
#             #headers start at 0 index so we want the second one with the event data and DSS keys
#             header = FT1File[1].header
#             ndskeys = header['NDSKEYS']
#         except:
#             try:
#                 header = FT1File[0].header
#                 ndskeys = header['NDSKEYS']
#                 self._headerNum = 0
#             except:
#                 showerror("Invalid File", "The file specified is not a valid Fermi data or counts map file.")
#                 return None
#         i = 1
#         isValid = False
#         while i <= ndskeys:  # we look through all the keys since they don't always have to be in the same order
#             key = 'DSTYP%i' %i
#             test = header[key]
#             if ('POS(RA,DEC)' == test):
#                 isValid = True
#                 break  # we found it so we don't need to keep looking
#             i += 1
#         if (isValid):
#             return FT1File
#         else:
#             showerror("Invalid File","No ROI position information found in file")
#             return None

#     def _checkCatalog(self):
#         """Determine the version of the catalog that is being used
#
#         Parameters:
#         - self - This CatalogSourceExtractor object
#
#         Return value:
#         - version - The version (1FGL, 2FLG, etc) of the catalog file or None if it is an invalid file
#
#         Usage:
#             catalogType = self._checkCatalog()
#             if (None == catalogType):
#                 #not a valid catalog file, handle error
#             # continue processing
#
#         Description:
#             This method opens up the catalog file specified by self.catParams.catalogFile and checks against
#         the known attributes of the various versions of the catalog files to determine the version number.  It
#         returns a None object if the file is not a Fermi catalog and the catalog name (1FGL, 2FGL, etc) if it is.
#         """
#         try:
#             fileCheck = pyfits.open(self.catParams['catalogFile'])
#             if ([] == fileCheck):
#                 return None # the file isn't a good FITS file
#         except:
#             return None # we have an invalid file
#
#         try:
#             test=fileCheck[1].data.field('Cutoff') #this field is only in the 2FGL catalog.  If it's not there it will throw an exception
#             fileCheck.close()
#             version = '2FGL'
#         except:
#             fileCheck.close()
#             version = '1FGL'
#
#         return version

#     def _getPos(self):
#         """Given that self.FT1File is valid extract the position and radius information
#
#         This method uses the DSS POS() keyword to extract the region of interest for
#         the source search to be conducted and returns the RA, Dec, and radius of the search region
#
#         usage:
#             RA,Dec,radius = self.getPos()
#
#         Modified from version in mak2FGLxml by Tyrel Johnson
#         """
#
#         header = self.FT1File[self._headerNum].header #use the header number determined in the fits file validation
#         ndskeys = header['NDSKEYS']
#         targetKey = 'POS(RA,DEC)'
#         i = 1
#         keyPosition = 0
#         while i <= ndskeys:  #this step is necessary since it is not clear that the POS key word will have the same number always
#             key = 'DSTYP%i' %i
#             test = header[key]
#             if(test == targetKey):
#                 keyPosition=i
#                 break # we found it so we don't need to keep looking
#             i+=1
#
#         #now we know the correct keyword position
#         keyword='DSVAL%i' % keyPosition
#         if ('circle' == header[keyword][:6]):  # The Science Tools only implement circular searches so just check for upper/lower case spelling
#             ra,dec,rad=header[keyword].strip('circle()').split(',') #gets rid of the circle and parenthesis part and splits around the comma
#         else:
#             ra,dec,rad=header[keyword].strip('CIRCLE()').split(',')
#         self.FT1File.close()  # we're done with the file
#         return float(ra),float(dec),float(rad)

    def _add1FGLSources(self):
        """Extract sources from the 1FGL catalog file

        Parameters:
        - self - This CatalogSourceExtractor object

        Return value:
        - none - Sets the self.sources variable to a list of source objects

        Usage:
           self._add1FGLSources()

        Description:
           This function loops over all of the sources in the 1FGL catalog file and extracts all those
        that lie within 5 degrees of the ROI.  It creates PowerLaw source objects for each.  Each model
        is added to the object's local list of sources.  The Galactic Diffuse source is added but with
        a fixed index of 0.  The user should modify this by hand if desired.
        """
#        file=pyfits.open(self.catParams['catalogFile'])
        file=self.catFile.fitsFilePtr
        data=file[1].data
        try:
            name=data.field('Source_Name')
        except:
            name=data.field('NickName')
        ra=data.field('RA')
        dec=data.field('DEC')
        flux=data.field('Flux_Density')
        pivot=data.field('Pivot_Energy')
        index=data.field('Spectral_Index')
        sigma=data.field('Signif_Avg')
        for n,f,i,r,d,p,s in zip(name,flux,index,ra,dec,pivot,sigma):
            dist=angsep(self.ra,self.dec,r,d) # get distance from object to ROI center
            if (r==self.ra and d==self.dec):  # just to avoid any small number errors
                dist = 0.0
            if (dist <= self.radius+5.0): # object is in target area
                fscale=int(floor(log10(f)))
                sourceName=''
                for N in n.split(' '):
                    sourceName+=N
                Name = (sourceName if not sourceName[0].isdigit() else "_"+sourceName) # add an underscore to prevent string/number issues if name starts with a digit
                source = Source(name = Name, type = "PointSource")
                self._PLspec(source,f,i,p,dist,s)
                ra = Parameter(name="RA",value = r, scale = 1.0, min = 0.0, max = 360.0, free = False)
                dec = Parameter(name="DEC",value = d, scale = 1.0, min = -90.0, max = 90.0, free = False)
                spatialModel = SpatialModel(type="SkyDirFunction",parameters=[ra,dec])
                source.setSpatialModel(spatialModel)
                if (None == self.sources):
                    self.sources = []
                self.sources.append(source)
        # Set Galactic Diffuse model
        gdSpatial = SpatialModel(type="MapCubeFunction", file=self.catParams['galDiffFile'])
        gdSource = Source(name=self.catParams['gdModelName'], type='DiffuseSource',spatialModel=gdSpatial) #default spectrum is PowerLaw
        # but we need to fix the index
        spec = gdSource.getSpectrum()
        index = spec.getParameterByName("Index")
        index.setFree(False)
        # and also set it to zero (why?  echoing Tyrel's script.  This probably won't be used much at all give the existence of 2FGL and soon 3FGL)
        index.setMax("1.0")
        index.setValue("0.0")
        spec.setParameterByName("Index",index)
        gdSource.setSpectrum(spec)
        self.sources.append(gdSource)

        # Set isotropic diffuse source
        if (None == self.catParams['isoTempFile']): #null means no file so assume user wants an isotropic power law component
            isoSpectrum = Specturm()  # create a default PowerLaw Spectrum
            Name='<source name="%s" type="DiffuseSource">\n' %ISOn
        else: #if a file is given assume it is an isotropic template
            isoSpectrum = Spectrum(type="FileFunction", file = self.catParams['isoTempFile'])
        #both of the above options use the same spatial model
        isoSpatial = SpatialModel(type="ConstantValue")
        isoSource = Source(name= self.catParams['isTempName'], type="DiffuseSource", spectrum=isoSpectrum, spatialModel=isoSpatial)
        self.sources.append(isoSource)

    def _add2FGLSources(self):
        """Extract sources from the 2FGL catalog file

        Parameters:
        - self - This CatalogSourceExtractor object

        Return value:
        - none - Sets the self.sources variable to a list of source objects

        Usage:
           self._add2FGLSources()

        Description:
            This function loops over all of the sources in the 2FGL catalog file and extracts all those
        that lie within 5 degrees of the ROI.  It creates Source objects for each on assigning it the
        appropriate spectral and spatial models based on the data provided in the catalog.  Each model
        is added to the object's local list of sources.

        """
        file = self.catFile.fitsFilePtr
#        file=pyfits.open(self.catParams['catalogFile']) #open source list file and access necessary fields, requires LAT source catalog definitions and names
        data=file[1].data
        extendedinfo=file[4].data
        extName=extendedinfo.field('Source_Name')
        extFile=extendedinfo.field('Spatial_Filename')
        name=data.field('Source_Name')
        ExtName=data.field('Extended_Source_Name')
        ra=data.field('RAJ2000')
        dec=data.field('DEJ2000')
        flux=data.field('Flux_Density')
        pivot=data.field('Pivot_Energy')
        index=data.field('Spectral_Index')
        cutoff=data.field('Cutoff')
        spectype=data.field('SpectrumType')
        beta=data.field('beta')
        sigma=data.field('Signif_Avg')
        ptSrcNum = 0
        extSrcNum = 0

        for n,f,i,r,d,p,c,t,b,S,EN in zip(name,flux,index,ra,dec,pivot,cutoff,spectype,beta,sigma,ExtName):
            dist=angsep(self.ra,self.dec,r,d) # get distance from object to ROI center
            if (r==self.ra and d==self.dec):  # just to avoid any small number errors
                dist = 0.0
            if (dist <= self.radius+5.0): # object is in target area
                sourceName=''
                for N in n.split(' '): # remove spaces from name
                    sourceName+=N
                if EN!='' and not self.catParams['forcePointSource']: # We're making an extended source model
                    extSrcNum+=1
                    Name = (EN if not EN[0].isdigit() else "_"+EN) # add an underscore to prevent string/number issues if name starts with a digit
                    Type = "DiffuseSource"
                else: # we're building a point source model
                    ptSrcNum+=1
                    Name = (sourceName if not sourceName[0].isdigit() else "_"+sourceName) # add an underscore to prevent string/number issues if name starts with a digit
                    Type = "PointSource"
                source = Source(name = Name, type = Type)
                if EN!='Vela X' and EN!='MSH 15-52':
                    if t=='PowerLaw':
                        self._PLspec(source,f,i,p,dist,S)
                    elif t=='PowerLaw2':#no value for flux from 100 MeV to 100 GeV in fits file0
                        if i!=1.:#so calculate it by integrating PowerLaw spectral model
                            F=f*p**i/(-i+1)*(1.e5**(-i+1)-1.e2**(-1+1))
                        else:
                            F=f*p*log(1.e3)
                        self._PL2spec(source,F,i,dist,S)
                    elif t=='LogParabola':
                        self._LPspec(source,f,i,p,b,dist,S)
                    else:
                        self._COspec(source,f,i,p,c,dist,S)
                else:
                    if EN=='Vela X':
                        self._VXspec(source,i,dist)
                    else:
                        self._MSHspec(source,i,dist)
                if EN!='' and not self.catParams['forcePointSource']:
                    eFile=None
                    for exN,exf in zip(extName,extFile):
                        if exN==EN:
                            if len(self.catParams['extTempDir'])>0:
                                if self.catParams['extTempDir'][-1]=='/':
                                    eFile=self.catParams['extTempDir']+exf
                                else:
                                    eFile=self.catParams['extTempDir']+'/'+exf
                            else:
                                eFile=exf
                            break
                    if eFile==None:
                        showError("The model template file for" + n + " does to seem to exist in the specified directory.  Please update model file parameter by hand.")
                        spatialModel = SpatialModel(type="SpatialMap",file = self.catParams['extTempDir'])
                    else:
                        spatialModel = SpatialModel(type="SpatialMap",file = eFile)
                else:
                    ra = Parameter(name="RA",value = r, scale = 1.0, min = 0.0, max = 360.0, free = False)
                    dec = Parameter(name="DEC",value = d, scale = 1.0, min = -90.0, max = 90.0, free = False)
                    spatialModel = SpatialModel(type="SkyDirFunction",parameters=[ra,dec])
                source.setSpatialModel(spatialModel)

                if (None == self.sources):
                    self.sources = []
                self.sources.append(source)

        # Set Galactic Diffuse model
        gdSpatial = SpatialModel(type="MapCubeFunction", file=self.catParams['galDiffFile'])
        gdSource = Source(name=self.catParams['gdModelName'], type='DiffuseSource',spatialModel=gdSpatial) #default spectrum is PowerLaw
        # but we need to fix the index
        spec = gdSource.getSpectrum()
        index = spec.getParameterByName("Index")
        index.setFree(False)
        spec.setParameterByName("Index",index)
        gdSource.setSpectrum(spec)
        self.sources.append(gdSource)

        # Set isotropic diffuse source
        if (None == self.catParams['isoTempFile']): #null means no file so assume user wants an isotropic power law component
            isoSpectrum = Specturm()  # create a default PowerLaw Spectrum
            Name='<source name="%s" type="DiffuseSource">\n' %ISOn
        else: #if a file is given assume it is an isotropic template
            isoSpectrum = Spectrum(type="FileFunction", file = self.catParams['isoTempFile'])
        #both of the above options use the same spatial model
        isoSpatial = SpatialModel(type="ConstantValue")
        isoSource = Source(name= self.catParams['isTempName'], type="DiffuseSource", spectrum=isoSpectrum, spatialModel=isoSpatial)
        self.sources.append(isoSource)

#        print "point source count =", ptSrcNum

        # @TODO Add in the diffuse sources

    def _add3FGLSources(self):
        """Extract sources from the 3FGL catalog file

        Parameters:
        - self - This CatalogSourceExtractor object

        Return value:
        - none - Sets the self.sources variable to a list of source objects

        Usage:
           self._add3FGLSources()

        Description:
            This function loops over all of the sources in the 3FGL catalog file and extracts all those
        that lie within 5 degrees of the ROI.  It creates Source objects for each on assigning it the
        appropriate spectral and spatial models based on the data provided in the catalog.  Each model
        is added to the object's local list of sources.

        """
        file = self.catFile.fitsFilePtr
#        file=pyfits.open(self.catParams['catalogFile']) #open source list file and access necessary fields, requires LAT source catalog definitions and names
        data=file[1].data
        extendedinfo=file[5].data
        extName=extendedinfo.field('Source_Name')
        extFile=extendedinfo.field('Spatial_Filename')
        name=data.field('Source_Name')
        ExtName=data.field('Extended_Source_Name')
        ra=data.field('RAJ2000')
        dec=data.field('DEJ2000')
        flux=data.field('Flux_Density')
        pivot=data.field('Pivot_Energy')
        index=data.field('Spectral_Index')
        cutoff=data.field('Cutoff')
        spectype=data.field('SpectrumType')
        beta=data.field('beta')
        sigma=data.field('Signif_Avg')
        ptSrcNum = 0
        extSrcNum = 0

        for n,f,i,r,d,p,c,t,b,S,EN in zip(name,flux,index,ra,dec,pivot,cutoff,spectype,beta,sigma,ExtName):
            dist=angsep(self.ra,self.dec,r,d) # get distance from object to ROI center
            if (r==self.ra and d==self.dec):  # just to avoid any small number errors
                dist = 0.0
            if (dist <= self.radius+5.0): # object is in target area
                sourceName=''
                for N in n.split(' '): # remove spaces from name
                    sourceName+=N
                if EN!='' and not self.catParams['forcePointSource']: # We're making an extended source model
                    extSrcNum+=1
                    Name = (EN if not EN[0].isdigit() else "_"+EN) # add an underscore to prevent string/number issues if name starts with a digit
                    Type = "DiffuseSource"
                else: # we're building a point source model
                    ptSrcNum+=1
                    Name = (sourceName if not sourceName[0].isdigit() else "_"+sourceName) # add an underscore to prevent string/number issues if name starts with a digit
                    Type = "PointSource"
                source = Source(name = Name, type = Type)
                if EN!='Vela X' and EN!='MSH 15-52':
                    if t=='PowerLaw':
                        self._PLspec(source,f,i,p,dist,S)
                    elif t=='PowerLaw2':#no value for flux from 100 MeV to 100 GeV in fits file0
                        if i!=1.:#so calculate it by integrating PowerLaw spectral model
                            F=f*p**i/(-i+1)*(1.e5**(-i+1)-1.e2**(-1+1))
                        else:
                            F=f*p*log(1.e3)
                        self._PL2spec(source,F,i,dist,S)
                    elif t=='LogParabola':
                        self._LPspec(source,f,i,p,b,dist,S)
                    else:
                        self._COspec(source,f,i,p,c,dist,S)
                else:
                    if EN=='Vela X':
                        self._VXspec(source,i,dist)
                    else:
                        self._MSHspec(source,i,dist)
                if EN!='' and not self.catParams['forcePointSource']:
                    eFile=None
                    for exN,exf in zip(extName,extFile):
                        if exN==EN:
                            if len(self.catParams['extTempDir'])>0:
                                if self.catParams['extTempDir'][-1]=='/':
                                    eFile=self.catParams['extTempDir']+exf
                                else:
                                    eFile=self.catParams['extTempDir']+'/'+exf
                            else:
                                eFile=exf
                            break
                    if eFile==None:
                        showError("The model template file for" + n + " does to seem to exist in the specified directory.  Please update model file parameter by hand.")
                        spatialModel = SpatialModel(type="SpatialMap",file = self.catParams['extTempDir'])
                    else:
                        spatialModel = SpatialModel(type="SpatialMap",file = eFile)
                else:
                    ra = Parameter(name="RA",value = r, scale = 1.0, min = 0.0, max = 360.0, free = False)
                    dec = Parameter(name="DEC",value = d, scale = 1.0, min = -90.0, max = 90.0, free = False)
                    spatialModel = SpatialModel(type="SkyDirFunction",parameters=[ra,dec])
                source.setSpatialModel(spatialModel)

                if (None == self.sources):
                    self.sources = []
                self.sources.append(source)

        # Set Galactic Diffuse model
        gdSpatial = SpatialModel(type="MapCubeFunction", file=self.catParams['galDiffFile'])
        gdSource = Source(name=self.catParams['gdModelName'], type='DiffuseSource',spatialModel=gdSpatial) #default spectrum is PowerLaw
        # but we need to fix the index
        spec = gdSource.getSpectrum()
        index = spec.getParameterByName("Index")
        index.setFree(False)
        spec.setParameterByName("Index",index)
        gdSource.setSpectrum(spec)
        self.sources.append(gdSource)

        # Set isotropic diffuse source
        if (None == self.catParams['isoTempFile']): #null means no file so assume user wants an isotropic power law component
            isoSpectrum = Specturm()  # create a default PowerLaw Spectrum
            Name='<source name="%s" type="DiffuseSource">\n' %ISOn
        else: #if a file is given assume it is an isotropic template
            isoSpectrum = Spectrum(type="FileFunction", file = self.catParams['isoTempFile'])
        #both of the above options use the same spatial model
        isoSpatial = SpatialModel(type="ConstantValue")
        isoSource = Source(name= self.catParams['isTempName'], type="DiffuseSource", spectrum=isoSpectrum, spatialModel=isoSpatial)
        self.sources.append(isoSource)

#        print "point source count =", ptSrcNum

        # @TODO Add in the diffuse sources
    def _PLspec(self,source,f,i,p,dist,sig):
        """Set parameters for a power law sepctrum source

        Parameters:
        - self - This CatalogSourceExtractor object
        - source - The Source object we are modifying
        - f - The flux of the source from the catalog
        - i - The spectral index of the source from the catalog
        - p - The pivot energy of the source from the catalog - used to set the Scale parameter
        - dist - Distance from source to ROI center
        - sig - Source significance from catalog

        Return value:
        - none - Sets the Spectrum component of the provided Source object

        Usage:
           self._PLspec(source,f,i,p,dist,S)

        Description:
            This method sets the necessary parameters for a PowerLaw spectrum source.  By default the
        parameters of the source are fixed unless the source is within the radius limit defined by the
        user for variable sources (which defaults to the extraction region from the FT1 file) and the
        source is above the specified significance limit (default 4).  In that case the Index and Prefactor
        parameters are allowed to vary.
            Note:  The index values (i) in the catalog are given as positive values (i.e. used in the form
        of flux = E^-i dE).  However the convention in the model editor seems to be to use negative values
        so the index sign is flipped when creating the source.  If it is desirable to use positive index
        values, simply swap out the current index parameter assignment for the one commented out.
        """
        fscale=int(floor(log10(f)))
        pfValue = f/10**fscale
        prefactor = Parameter(name="Prefactor",value = pfValue, scale = 10**fscale, min = 0.001, max = 1000.0, free = False)
        index = Parameter(name="Index",value = -i, scale = 1.0, min = -6.0, max = -1.0, free = False) #flip the sign, positive in catalog but negative here
#        index = Parameter(name="Index",value = i, scale = -1.0, min = 1.0, max = 5.0, free = False) # use this one if you want to have positive index values
        scale = Parameter(name="Scale",value = p, scale = 1.0, min = 30.0, max = 5e5, free = False)
        if (dist<=self.radLim and dist <= self.radius and sig >= self.catParams['sigLimit']):
            index.setFree(True)
            prefactor.setFree(True)
        spectrum = Spectrum(type='PowerLaw',parameters=[prefactor,index,scale])
        source.setSpectrum(spectrum)

    def _PL2spec(self,source,F,i,dist,sig):
        """Set parameters for a PowerLaw2 sepctrum source

        Parameters:
        - self - This CatalogSourceExtractor object
        - source - The Source object we are modifying
        - F - The integrated flux of the source calculated from the catalog parameters
        - i - The spectral index of the source from the catalog
        - dist - Distance from source to ROI center
        - sig - Source significance from catalog

        Return value:
        - none - Sets the Spectrum component of the provided Source object

        Usage:
           self._PL2spec(self,source,F,i,dist,sig)

        Description:
            This method sets the necessary parameters for a LogParabola spectrum source.  By default the
        parameters of the source are fixed unless the source is within the radius limit defined by the
        user for variable sources (which defaults to the extraction region from the FT1 file) and the
        source is above the specified significance limit (default 4).  In that case the Integral and Index
        parameters are allowed to vary.
            Note:  The index values (i) in the catalog are given as positive values (i.e. used in the form
        of flux = E^-i dE).  However the convention in the model editor seems to be to use negative values
        so the index sign is flipped when creating the source.  If it is desirable to use positive index
        values, simply swap out the current index parameter assignment for the one commented out.
        """
        fscale=int(floor(log10(F)))
        pfValue = F/10**fscale
        integral = Parameter(name="Integral",value = pfValue, scale = 10**fscale, min = 0.0001, max = 10000.0, free = False)
        index = Parameter(name="Index",value = -i, scale = 1.0, min = -5.0, max = -1.0, free = False) #flip the sign, positive in catalog but negative here
#        index = Parameter(name="Index",value = i, scale = -1.0, min = 1.0, max = 5.0, free = False) # use this one if you want to have positive index values
        lowerLimit = Parameter(name="LowerLimit",value = 100, scale = 1.0, min = 30.0, max = 5e5, free = False)
        upperLimit = Parameter(name="UpperLimit",value = 1e5, scale = 1.0, min = 30.0, max = 5e5, free = False)
        if (dist<=self.radLim and dist <= self.radius and sig >= self.catParams['sigLimit']):
            index.setFree(True)
            integral.setFree(True)
        spectrum = Spectrum(type='PowerLaw2',parameters=[integral,index,lowerLimit,upperLimit])
        source.setSpectrum(spectrum)

    def _LPspec(self,source,f,i,p,b,dist,sig):
        """Set parameters for a LogParabola sepctrum source

        Parameters:
        - self - This CatalogSourceExtractor object
        - source - The Source object we are modifying
        - F - The integrated flux of the source calculated from the catalog parameters
        - i - The spectral index of the source from the catalog
        - p - The pivot energy of the source from the catalog - used to set the Eb parameter
        - b - The beta index from the catalog
        - dist - Distance from source to ROI center
        - sig - Source significance from catalog

        Return value:
        - none - Sets the Spectrum component of the provided Source object

        Usage:
           self._LPspec(self,source,f,i,p,b,dist,sig)

        Description:
           This method sets the necessary parameters for a PowerLaw2 spectrum source.  By default the
        parameters of the source are fixed unless the source is within the radius limit defined by the
        user for variable sources (which defaults to the extraction region from the FT1 file) and the
        source is above the specified significance limit (default 4).  In that case the norm, alpha, and
        beta parameters are allowed to vary.
             Note:  The index values (i & b) in the catalog are given as positive values (i.e. used in the form
        of flux = E^-i dE).  However the convention in the model editor seems to be to use negative values
        so the index sign is flipped when creating the source.  If it is desirable to use positive index
        values, simply swap out the current index parameter assignment for the one commented out.
        """
        fscale=int(floor(log10(f)))
        pfValue = f/10**fscale
        norm  = Parameter(name="norm",value = pfValue, scale = 10**fscale, min = 0.0001, max = 10000.0, free = False)
        alpha = Parameter(name="alpha",value = -i, scale = 1.0, min = -5.0, max = 0, free = False) # flip the sign, positive in catalog but negative here
        beta  = Parameter(name="beta",value = -b, scale = 1.0, min = -10.0, max = 0, free = False) # flip the sign, positive in catalog but negative here
#        alpha = Parameter(name="alpha",value = i, scale = -1.0, min = 0, max = 5.0, free = False)  # use this one if you want to have positive index values
#        beta  = Parameter(name="beta",value = b, scale = -1.0, min = 0, max = 10.0, free = False)  # use this one if you want to have positive index values
        Eb  = Parameter(name="Eb",value = p, scale = 1.0, min = 30., max = 5e5, free = False) # flip the sign, positive in catalog but negative here
        if (dist<=self.radLim and dist <= self.radius and sig >= self.catParams['sigLimit']):
            alpha.setFree(True)
            beta.setFree(True)
            integral.setFree(True)
        spectrum = Spectrum(type='LogParabola',parameters=[norm,alpha,beta,Eb])
        source.setSpectrum(spectrum)

    def _COspec(self,source,f,i,p,c,dist,sig):
        """Set parameters for a PLSuperExpCutoff sepctrum source

        Parameters:
        - self - This CatalogSourceExtractor object
        - source - The Source object we are modifying
        - f - The flux of the source from the catalog
        - i - The spectral index of the source from the catalog
        - p - The pivot energy of the source from the catalog - used to set the Scale parameter
        - c - The cutoff energy from the catalog
        - dist - Distance from source to ROI center
        - sig - Source significance from catalog

        Return value:
        - none - Sets the Spectrum component of the provided Source object

        Usage:
           self._COspec(self,source,f,i,p,c,dist,sig)

        Description:
            This method sets the necessary parameters for a PLSuperExpCutoff spectrum source.  By default the
        parameters of the source are fixed unless the source is within the radius limit defined by the
        user for variable sources (which defaults to the extraction region from the FT1 file) and the
        source is above the specified significance limit (default 4).  In that case the Index1, Cutoff, and
        Prefactor parameters are allowed to vary.
            Note:  The index values (i) in the catalog are given as positive values (i.e. used in the form
        of flux = E^-i dE).  However the convention in the model editor seems to be to use negative values
        so the index sign is flipped when creating the source.  If it is desirable to use positive index
        values, simply swap out the current index parameter assignment for the one commented out.
        """
        fscale=int(floor(log10(f)))
        pfValue = f/10**fscale
        prefactor = Parameter(name="Prefactor",value = pfValue, scale = 10**fscale, min = 0.001, max = 1000.0, free = False)
        index1 = Parameter(name="Index1",value = -i, scale = 1.0, min = -5.0, max = 0, free = False) #flip the sign, positive in catalog but negative here
        index2 = Parameter(name="Index2",value = -1.0, scale = 1.0, min = -5.0, max = 0, free = False) #flip the sign, positive in catalog but negative here
#        index = Parameter(name="Index",value = i, scale = -1.0, min = 0, max = 5.0, free = False) # use this one if you want to have positive index values
#        index2 = Parameter(name="Index2",value = 1.0, scale = -1.0, min = 0, max = 5.0, free = False) #flip the sign, positive in catalog but negative here
        if c<=1e5:
            cutoff = Parameter(name="Cutoff", value = c , scale = 1.0, min = 10, max = 1e5)
        else:
            cutoff = Parameter(name="Cutoff", value = c , scale = 1.0, min = 10, max = 2*c)
        scale = Parameter(name="Scale",value = p, scale = 1.0, min = 30.0, max = 5e5, free = False)
        if (dist<=self.radLim and dist <= self.radius and sig >= self.catParams['sigLimit']):
            index1.setFree(True)
            if c<=1e5:cutoff.setFree(True)
            prefactor.setFree(True)
        spectrum = Spectrum(type='PLSuperExpCutoff',parameters=[prefactor,index1,scale,cutoff,index2])
        source.setSpectrum(spectrum)

    def _VXspec(self,source,i,dist):
        """Set parameters for the Vela X source

        Parameters:
        - self - This CatalogSourceExtractor object
        - source - The Source object we are modifying
        - i - The spectral index of the source from the catalog
        - dist - Distance from source to ROI center - not used

        Return value:
        - none - Sets the Spectrum component of the provided Source object

        Usage:
           self._VXspec(self,source,i,dist)

        Description:
            This method sets the necessary parameters for a Vela X source.  By default all parameters
        of the source are fixed.
            Note:  The index values (i) in the catalog are given as positive values (i.e. used in the form
        of flux = E^-i dE).  However the convention in the model editor seems to be to use negative values
        so the index sign is flipped when creating the source.  If it is desirable to use positive index
        values, simply swap out the current index parameter assignment for the one commented out.
        """
        integral = Parameter(name="Integral",value = 4.73, scale = 1e-7, min = 0.0001, max = 10000.0, free = False)
        index = Parameter(name="Index",value = -i, scale = 1.0, min = -5.0, max = -1.0, free = False) #flip the sign, positive in catalog but negative here
#        index = Parameter(name="Index",value = i, scale = -1.0, min = 1.0, max = 5.0, free = False) # use this one if you want to have positive index values
        lowerLimit = Parameter(name="LowerLimit",value = 100, scale = 1.0, min = 30.0, max = 5e5, free = False)
        upperLimit = Parameter(name="UpperLimit",value = 2e5, scale = 1.0, min = 30.0, max = 5e5, free = False)
        spectrum = Spectrum(type='PowerLaw2',parameters=[integral,index,lowerLimit,upperLimit])
        source.setSpectrum(spectrum)

    def _MSHspec(self,source,i,dist):
        """Set parameters for the MSH 15-52 source

        Parameters:
        - self - This CatalogSourceExtractor object
        - source - The Source object we are modifying
        - i - The spectral index of the source from the catalog
        - dist - Distance from source to ROI center - not used

        Return value:
        - none - Sets the Spectrum component of the provided Source object

        Usage:
           self._VXspec(self,source,i,dist)

        Description:
            This method sets the necessary parameters for a MSH 15-52 source.  By default all parameters
        of the source are fixed.
            Note:  The index values (i) in the catalog are given as positive values (i.e. used in the form
        of flux = E^-i dE).  However the convention in the model editor seems to be to use negative values
        so the index sign is flipped when creating the source.  If it is desirable to use positive index
        values, simply swap out the current index parameter assignment for the one commented out.
        """
        integral = Parameter(name="Integral",value = 0.291, scale = 1e-8, min = 0.0001, max = 10000.0, free = False)
        index = Parameter(name="Index",value = -i, scale = 1.0, min = -5.0, max = -1.0, free = False) #flip the sign, positive in catalog but negative here
#        index = Parameter(name="Index",value = i, scale = -1.0, min = 1.0, max = 5.0, free = False) # use this one if you want to have positive index values
        lowerLimit = Parameter(name="LowerLimit",value = 1000, scale = 1.0, min = 30.0, max = 5e5, free = False)
        upperLimit = Parameter(name="UpperLimit",value = 1e5, scale = 1.0, min = 30.0, max = 5e5, free = False)
        spectrum = Spectrum(type='PowerLaw2',parameters=[integral,index,lowerLimit,upperLimit])
        source.setSpectrum(spectrum)

def angsep(ra1,dec1,ra2,dec2):
    """Compute the angular separations between two points on a sphere

    Parameters:
    - ra1 - Right ascension of first position
    - dec1 - Declination of first position
    - ra2 - Right ascension of second position
    - dec2 - Declination of second position
        Note:  All input parameters are expected to be in degrees

    Return value:
    - angSep - the angular separation of the two positions in degrees

    Usage:
        angSep = angsep(ra1,dec1,ra2,dec2)

    Description:
       Using spherical trig, this method computers the angular separation of
    two points on the celestial sphere
    """
    ra1*=d2r
    dec1*=d2r
    ra2*=d2r
    dec2*=d2r
    diffCosine=cos(dec1)*cos(dec2)*cos(ra1-ra2)+sin(dec1)*sin(dec2)
    dC='%.10f'%diffCosine#when the source is right at the center of the roi python sometimes adds extraneous digits at the end of the value i.e. instead of 1.0
    #it returns 1.0000000000000024, which throws an error with the acos function
    return acos(float(dC))/d2r #returns values between 0 and 180 degrees

if __name__ == '__main__':
    testParams = {'eventFile': '/home/tstephen/Downloads/LAT/L13120916430237B0217980_PH00.fits',
                  'isTempName': 'Extragalactic Diffuse',
                  'isoTempFile': '/home/tstephen/FSSC/ST/ScienceTools-ST_DEV/x86_64-unknown-linux-gnu-libc2.12/refdata/fermi/galdiffuse/isotrop_4years_P7_v9_repro_source_v1.txt',
#                  'catalogFile': '/home/tstephen/Downloads/LAT/gll_psc_v03.fit', # 1FGL
                  'catalogFile': '/home/tstephen/Downloads/LAT/gll_psc_v08.fit', # 2FGL
                  'sigLimit': '4',
                  'galDiffFile': '/home/tstephen/FSSC/ST/ScienceTools-ST_DEV/x86_64-unknown-linux-gnu-libc2.12/refdata/fermi/galdiffuse/gll_iem_v06.fits',
                  'gdModelName': 'GAL_v02',
                  'radiusLimit': '-1',
                  'forcePointSource': False,
                  'extTempDir':  '/home/tstephen/Downloads/LAT/Templates'
    }
    extractor = CatalogSourceExtractor(testParams)
    sources = extractor.getSources()
    print sources
